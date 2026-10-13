"""Plugin registration, discovery, installation, and lifecycle management.

Author: Taylor B. | Inspyre-Softworks.
"""

from collections.abc import Iterable
from dataclasses import dataclass
import importlib.util
from importlib.metadata import entry_points
import json
from pathlib import Path
import shutil
import sys
from threading import Thread

from platformdirs import user_data_path
from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from inspyred_dev.plugins.api import (
    ApplicationPlugin,
    PluginContribution,
    PluginMetadata,
    PluginServices,
)
from inspyred_dev.plugins.installer import (
    InstalledPluginManifest,
    PluginInstallError,
    install_plugin_archive,
    read_manifest,
)


ENTRY_POINT_GROUP = 'inspyred_dev.plugins'
DISABLED_SETTING = 'plugins/disabledIds'
PENDING_REMOVAL_SETTING = 'plugins/pendingRemovalIds'


class PluginError(RuntimeError):
    """Report an invalid plugin or conflicting plugin contribution."""


@dataclass
class _PluginRecord:
    metadata: PluginMetadata
    origin: str
    plugin: ApplicationPlugin | None = None
    install_path: Path | None = None
    enabled: bool = True
    active: bool = False
    error: str = ''
    pending_removal: bool = False


class PluginRegistry(QObject):
    """Own plugins and expose installation and lifecycle controls to QML."""

    pluginsChanged = Signal()
    operationStateChanged = Signal()
    _installFinished = Signal(bool, str)

    def __init__(
        self,
        plugins: Iterable[ApplicationPlugin] = (),
        settings: QSettings | None = None,
        user_plugin_dir: Path | None = None,
    ) -> None:
        """Register bundled plugins and restore persistent plugin preferences."""
        super().__init__()
        self._settings = settings or QSettings('Inspyre-Softworks', 'Inspyred Dev')
        self._user_plugin_dir = user_plugin_dir or (
            user_data_path('Inspyred Dev', 'Inspyre-Softworks') / 'plugins'
        )
        self._disabled_ids = self._string_set(DISABLED_SETTING)
        self._pending_removal_ids = self._string_set(PENDING_REMOVAL_SETTING)
        self._records: dict[str, _PluginRecord] = {}
        self._active: list[ApplicationPlugin] = []
        self._qml_context: dict[str, QObject] = {}
        self._qml_import_paths: list[Path] = []
        self._ui_extensions: dict[str, list[dict[str, str]]] = {}
        self._operation_busy = False
        self._operation_message = ''
        self._operation_error = ''
        self._installFinished.connect(self._handle_install_finished)
        self._apply_pending_removals()
        for plugin in plugins:
            self.register(plugin, origin='bundled')

    def _string_set(self, key: str) -> set[str]:
        value = self._settings.value(key, [])
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                decoded = [value] if value else []
            value = decoded
        if not isinstance(value, (list, tuple, set)):
            return set()
        return {str(item) for item in value if str(item)}

    def _save_ids(self, key: str, values: set[str]) -> None:
        self._settings.setValue(key, json.dumps(sorted(values)))

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        """Return registered plugin identifiers in display order."""
        return tuple(self._records)

    @property
    def qml_context(self) -> dict[str, QObject]:
        """Return a copy of the context objects contributed by active plugins."""
        return dict(self._qml_context)

    @property
    def qml_import_paths(self) -> tuple[Path, ...]:
        """Return QML import paths contributed by active plugins."""
        return tuple(self._qml_import_paths)

    @Property(list, notify=pluginsChanged)
    def installedPlugins(self) -> list[dict[str, object]]:  # noqa: N802
        """Return plugin inventory records for the About window."""
        return [
            {
                'id': plugin_id,
                'name': record.metadata.name,
                'version': record.metadata.version,
                'origin': {
                    'bundled': 'Built in',
                    'entry_point': 'Python package',
                    'user': 'User plugin',
                }.get(record.origin, record.origin),
                'enabled': record.enabled,
                'active': record.active,
                'error': record.error,
                'pendingRemoval': record.pending_removal,
                'canDisable': record.origin != 'bundled',
                'canUninstall': record.origin == 'user',
            }
            for plugin_id, record in self._records.items()
        ]

    @Property(bool, notify=operationStateChanged)
    def operationBusy(self) -> bool:  # noqa: N802
        """Return whether a plugin archive is being installed."""
        return self._operation_busy

    @Property(str, notify=operationStateChanged)
    def operationMessage(self) -> str:  # noqa: N802
        """Return the latest successful plugin-management message."""
        return self._operation_message

    @Property(str, notify=operationStateChanged)
    def operationError(self) -> str:  # noqa: N802
        """Return the latest plugin-management error."""
        return self._operation_error

    def register(self, plugin: ApplicationPlugin, origin: str = 'bundled') -> None:
        """Register one plugin and reject ambiguous identifiers."""
        if not isinstance(plugin, ApplicationPlugin):
            raise PluginError('Plugin does not implement the Inspyred Dev plugin contract.')
        metadata = plugin.metadata
        plugin_id = metadata.plugin_id.strip()
        if not plugin_id:
            raise PluginError('Plugin IDs cannot be empty.')
        if plugin_id in self._records:
            raise PluginError(f'Duplicate plugin ID: {plugin_id}')
        enabled = origin == 'bundled' or plugin_id not in self._disabled_ids
        self._records[plugin_id] = _PluginRecord(metadata, origin, plugin, enabled=enabled)

    def discover(self, group: str = ENTRY_POINT_GROUP) -> None:
        """Load Python entry-point and user-directory plugins."""
        for entry_point in entry_points().select(group=group):
            try:
                loaded = entry_point.load()
                plugin = loaded() if isinstance(loaded, type) else loaded
                self.register(plugin, origin='entry_point')
            except Exception as error:
                plugin_id = f'entry-point:{entry_point.name}'
                self._records[plugin_id] = _PluginRecord(
                    PluginMetadata(plugin_id, entry_point.name, 'Unknown'),
                    'entry_point',
                    error=str(error),
                )
        self._discover_user_plugins()

    def _discover_user_plugins(self, load_enabled: bool = True) -> None:
        if not self._user_plugin_dir.is_dir():
            return
        for child in sorted(self._user_plugin_dir.iterdir()):
            if not child.is_dir() or child.name.startswith('.'):
                continue
            try:
                manifest = read_manifest(child)
            except PluginInstallError as error:
                plugin_id = f'invalid:{child.name}'
                self._records[plugin_id] = _PluginRecord(
                    PluginMetadata(plugin_id, child.name, 'Unknown'),
                    'user',
                    install_path=child,
                    enabled=False,
                    error=str(error),
                )
                continue
            existing = self._records.get(manifest.plugin_id)
            if existing is not None:
                if existing.origin == 'user':
                    existing.metadata = PluginMetadata(
                        manifest.plugin_id, manifest.name, manifest.version
                    )
                    existing.install_path = manifest.root
                continue
            enabled = manifest.plugin_id not in self._disabled_ids
            record = _PluginRecord(
                PluginMetadata(manifest.plugin_id, manifest.name, manifest.version),
                'user',
                install_path=manifest.root,
                enabled=enabled,
            )
            self._records[manifest.plugin_id] = record
            if enabled and load_enabled:
                try:
                    record.plugin = self._load_user_plugin(manifest)
                except Exception as error:
                    record.error = str(error)

    @staticmethod
    def _load_user_plugin(manifest: InstalledPluginManifest) -> ApplicationPlugin:
        module_name, object_name = manifest.entry_point.split(':', 1)
        module_file = manifest.root / f'{module_name}.py'
        is_package = not module_file.is_file()
        if is_package:
            module_file = manifest.root / module_name / '__init__.py'
        unique_name = f'_inspyred_plugin_{manifest.plugin_id.replace("-", "_").replace(".", "_")}'
        specification = importlib.util.spec_from_file_location(
            unique_name,
            module_file,
            submodule_search_locations=[str(module_file.parent)] if is_package else None,
        )
        if specification is None or specification.loader is None:
            raise PluginError('The plugin entry-point module could not be loaded.')
        module = importlib.util.module_from_spec(specification)
        sys.modules[unique_name] = module
        specification.loader.exec_module(module)
        loaded = getattr(module, object_name)
        plugin = loaded() if isinstance(loaded, type) else loaded
        if not isinstance(plugin, ApplicationPlugin):
            raise PluginError('The installed plugin does not implement ApplicationPlugin.')
        if plugin.metadata.plugin_id != manifest.plugin_id:
            raise PluginError('The plugin metadata ID does not match its manifest ID.')
        return plugin

    def activate_all(self, services: PluginServices) -> None:
        """Activate enabled plugins and merge their Qt contributions."""
        if self._active:
            raise PluginError('Plugins have already been activated.')
        for plugin_id, record in self._records.items():
            plugin = record.plugin
            if not record.enabled or plugin is None or record.error:
                continue
            try:
                contribution = plugin.activate(services)
                self._accept_contribution(plugin, contribution)
            except Exception as error:
                plugin.deactivate()
                if record.origin == 'bundled':
                    self.deactivate_all()
                    raise
                record.error = str(error)
                continue
            record.active = True
            self._active.append(plugin)
        self.pluginsChanged.emit()

    def _accept_contribution(
        self,
        plugin: ApplicationPlugin,
        contribution: PluginContribution,
    ) -> None:
        if not isinstance(contribution, PluginContribution):
            raise PluginError(
                f'Plugin {plugin.metadata.plugin_id} returned an invalid contribution.'
            )
        duplicates = self._qml_context.keys() & contribution.qml_context.keys()
        if duplicates:
            names = ', '.join(sorted(duplicates))
            raise PluginError(f'Plugin {plugin.metadata.plugin_id} conflicts on QML names: {names}')
        self._qml_context.update(contribution.qml_context)
        for path in contribution.qml_import_paths:
            resolved = path.resolve()
            if resolved not in self._qml_import_paths:
                self._qml_import_paths.append(resolved)
        for extension in contribution.ui_extensions:
            if not extension.slot.strip():
                raise PluginError(f'Plugin {plugin.metadata.plugin_id} has an empty UI slot.')
            source = extension.source.resolve()
            if not source.is_file():
                raise PluginError(
                    f'Plugin {plugin.metadata.plugin_id} UI component does not exist: {source}'
                )
            self._ui_extensions.setdefault(extension.slot, []).append(
                {
                    'pluginId': plugin.metadata.plugin_id,
                    'pluginName': plugin.metadata.name,
                    'source': source.as_uri(),
                }
            )

    @Slot(str, result='QVariantList')
    def uiExtensions(self, slot: str) -> list[dict[str, str]]:  # noqa: N802
        """Return plugin UI components registered for one extension point."""
        return list(self._ui_extensions.get(slot, ()))

    @Slot(str)
    def installPlugin(self, source: str) -> None:  # noqa: N802
        """Install a local or GitHub-hosted plugin ZIP without blocking the UI."""
        if self._operation_busy:
            return
        self._operation_busy = True
        self._operation_message = ''
        self._operation_error = ''
        self.operationStateChanged.emit()
        reserved_ids = set(self._records)

        def install() -> None:
            try:
                manifest = install_plugin_archive(
                    source,
                    self._user_plugin_dir,
                    reserved_ids=reserved_ids,
                )
                self._installFinished.emit(
                    True,
                    f'{manifest.name} {manifest.version} was installed. Restart to enable it.',
                )
            except Exception as error:
                self._installFinished.emit(False, str(error))

        Thread(target=install, daemon=True).start()

    @Slot(bool, str)
    def _handle_install_finished(self, succeeded: bool, message: str) -> None:
        self._operation_busy = False
        if succeeded:
            self._operation_message = message
            self._operation_error = ''
            self._discover_user_plugins(load_enabled=False)
            self.pluginsChanged.emit()
        else:
            self._operation_message = ''
            self._operation_error = message
        self.operationStateChanged.emit()

    @Slot(str, bool)
    def setPluginEnabled(self, plugin_id: str, enabled: bool) -> None:  # noqa: N802
        """Persist whether a non-bundled plugin should load on the next launch."""
        record = self._records.get(plugin_id)
        if record is None or record.origin == 'bundled' or record.enabled == enabled:
            return
        record.enabled = enabled
        if enabled:
            self._disabled_ids.discard(plugin_id)
        else:
            self._disabled_ids.add(plugin_id)
        self._save_ids(DISABLED_SETTING, self._disabled_ids)
        self._operation_error = ''
        self._operation_message = 'Plugin preference saved. Restart Inspyred Dev to apply it.'
        self.pluginsChanged.emit()
        self.operationStateChanged.emit()

    @Slot(str)
    def uninstallPlugin(self, plugin_id: str) -> None:  # noqa: N802
        """Remove a user plugin now or queue active files for removal on restart."""
        record = self._records.get(plugin_id)
        if record is None or record.origin != 'user' or record.install_path is None:
            return
        if record.active:
            record.enabled = False
            record.pending_removal = True
            self._disabled_ids.add(plugin_id)
            self._pending_removal_ids.add(plugin_id)
            self._save_ids(DISABLED_SETTING, self._disabled_ids)
            self._save_ids(PENDING_REMOVAL_SETTING, self._pending_removal_ids)
            message = 'Plugin will be removed when Inspyred Dev restarts.'
        else:
            try:
                self._remove_user_plugin(plugin_id, record.install_path)
            except OSError as error:
                self._operation_error = f'Could not remove the plugin: {error}'
                self.operationStateChanged.emit()
                return
            self._records.pop(plugin_id, None)
            self._disabled_ids.discard(plugin_id)
            self._save_ids(DISABLED_SETTING, self._disabled_ids)
            message = 'Plugin removed.'
        self._operation_error = ''
        self._operation_message = message
        self.pluginsChanged.emit()
        self.operationStateChanged.emit()

    def _remove_user_plugin(self, plugin_id: str, path: Path) -> None:
        target = path.resolve()
        expected = (self._user_plugin_dir / plugin_id).resolve()
        if target != expected or target.parent != self._user_plugin_dir.resolve():
            raise OSError('Plugin path is outside the managed plugin directory.')
        if target.is_dir():
            shutil.rmtree(target)

    def _apply_pending_removals(self) -> None:
        remaining: set[str] = set()
        for plugin_id in self._pending_removal_ids:
            try:
                self._remove_user_plugin(plugin_id, self._user_plugin_dir / plugin_id)
            except OSError:
                remaining.add(plugin_id)
            else:
                self._disabled_ids.discard(plugin_id)
        self._pending_removal_ids = remaining
        self._save_ids(PENDING_REMOVAL_SETTING, remaining)
        self._save_ids(DISABLED_SETTING, self._disabled_ids)

    def deactivate_all(self) -> None:
        """Deactivate active plugins in reverse order and clear contributions."""
        for plugin in reversed(self._active):
            plugin.deactivate()
        for record in self._records.values():
            record.active = False
        self._active.clear()
        self._qml_context.clear()
        self._qml_import_paths.clear()
        self._ui_extensions.clear()
        self.pluginsChanged.emit()
