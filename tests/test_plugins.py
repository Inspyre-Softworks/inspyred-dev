"""Tests for plugin contributions and lifecycle behavior."""

from dataclasses import dataclass
import json
from pathlib import Path
import zipfile

import pytest
from PySide6.QtCore import QObject, QSettings, Signal, Slot

from inspyred_dev.plugins import (
    PluginContribution,
    PluginError,
    PluginMetadata,
    PluginRegistry,
    PluginServices,
    PluginUiExtension,
)
from inspyred_dev.plugins.github import GitHubPlugin
from inspyred_dev.plugins.installer import PluginInstallError, install_plugin_archive


class _Object(QObject):
    pass


@dataclass
class _Plugin:
    plugin_id: str
    context_name: str
    ui_source: Path | None = None
    deactivated: bool = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(self.plugin_id, self.plugin_id.title(), '1.0')

    def activate(self, services: PluginServices) -> PluginContribution:
        extensions = (
            (PluginUiExtension('settings.integrations', self.ui_source),)
            if self.ui_source is not None
            else ()
        )
        return PluginContribution({self.context_name: _Object()}, ui_extensions=extensions)

    def deactivate(self) -> None:
        self.deactivated = True


class _GitHubController(QObject):
    issueCreated = Signal(int, int, str)


class _Observations(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.linked: tuple[int, int, str] | None = None

    @Slot(int, int, str)
    def linkGithubIssue(self, observation_id: int, issue_number: int, issue_url: str) -> None:
        self.linked = (observation_id, issue_number, issue_url)


def _services(observations: QObject | None = None) -> PluginServices:
    return PluginServices(_Object(), _Object(), observations or _Object())


def _plugin_zip(tmp_path: Path, plugin_id: str = 'sample-plugin') -> Path:
    archive = tmp_path / f'{plugin_id}.zip'
    manifest = {
        'id': plugin_id,
        'name': 'Sample Plugin',
        'version': '1.2.3',
        'entry_point': 'plugin:Plugin',
    }
    plugin_source = """
from inspyred_dev.plugins import PluginContribution, PluginMetadata

class Plugin:
    @property
    def metadata(self):
        return PluginMetadata('sample-plugin', 'Sample Plugin', '1.2.3')

    def activate(self, services):
        return PluginContribution()

    def deactivate(self):
        pass
"""
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('repository-main/inspyred-plugin.json', json.dumps(manifest))
        bundle.writestr('repository-main/plugin.py', plugin_source)
    return archive


def test_registry_combines_context_and_ui_extensions(tmp_path) -> None:
    """Expose multiple plugins through the same context and UI contracts."""
    first_view = tmp_path / 'First.qml'
    second_view = tmp_path / 'Second.qml'
    first_view.write_text('Item {}', encoding='utf-8')
    second_view.write_text('Item {}', encoding='utf-8')
    first = _Plugin('first', 'First', first_view)
    second = _Plugin('second', 'Second', second_view)
    registry = PluginRegistry([first, second])

    registry.activate_all(_services())

    assert registry.plugin_ids == ('first', 'second')
    assert set(registry.qml_context) == {'First', 'Second'}
    extensions = registry.uiExtensions('settings.integrations')
    assert [extension['pluginId'] for extension in extensions] == ['first', 'second']
    assert all(extension['source'].startswith('file:') for extension in extensions)

    registry.deactivate_all()
    assert first.deactivated
    assert second.deactivated
    assert registry.qml_context == {}
    assert registry.uiExtensions('settings.integrations') == []


def test_registry_rejects_duplicate_plugin_and_context_names() -> None:
    """Keep plugin identity and QML globals unambiguous."""
    with pytest.raises(PluginError, match='Duplicate plugin ID'):
        PluginRegistry([_Plugin('same', 'One'), _Plugin('same', 'Two')])

    registry = PluginRegistry([_Plugin('one', 'Shared'), _Plugin('two', 'Shared')])
    with pytest.raises(PluginError, match='conflicts on QML names'):
        registry.activate_all(_services())


def test_github_plugin_owns_controller_ui_and_issue_link_wiring() -> None:
    """Load GitHub through the same generic contract available to future plugins."""
    controller = _GitHubController()
    observations = _Observations()
    plugin = GitHubPlugin(controller_factory=lambda: controller)
    registry = PluginRegistry([plugin])

    registry.activate_all(_services(observations))
    controller.issueCreated.emit(7, 42, 'https://github.com/example/repo/issues/42')

    assert registry.qml_context['GitHubAuth'] is controller
    assert registry.uiExtensions('settings.integrations')[0]['pluginId'] == 'github'
    assert observations.linked == (7, 42, 'https://github.com/example/repo/issues/42')

    registry.deactivate_all()
    observations.linked = None
    controller.issueCreated.emit(8, 43, 'https://github.com/example/repo/issues/43')
    assert observations.linked is None


def test_install_and_discover_manifest_plugin(tmp_path) -> None:
    """Install a GitHub-style ZIP and load its declared plugin on next startup."""
    plugin_directory = tmp_path / 'plugins'
    manifest = install_plugin_archive(str(_plugin_zip(tmp_path)), plugin_directory)
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    registry = PluginRegistry(settings=settings, user_plugin_dir=plugin_directory)

    registry.discover(group='unused.test.group')
    registry.activate_all(_services())

    assert manifest.plugin_id == 'sample-plugin'
    assert registry.plugin_ids == ('sample-plugin',)
    assert registry.installedPlugins[0]['active']
    assert registry.installedPlugins[0]['origin'] == 'User plugin'


def test_disable_and_uninstall_user_plugin_are_persistent(tmp_path) -> None:
    """Remember disabled state and remove inactive managed plugin files."""
    plugin_directory = tmp_path / 'plugins'
    install_plugin_archive(str(_plugin_zip(tmp_path)), plugin_directory)
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    registry = PluginRegistry(settings=settings, user_plugin_dir=plugin_directory)
    registry.discover(group='unused.test.group')

    registry.setPluginEnabled('sample-plugin', False)
    assert not registry.installedPlugins[0]['enabled']

    restored = PluginRegistry(settings=settings, user_plugin_dir=plugin_directory)
    restored.discover(group='unused.test.group')
    assert not restored.installedPlugins[0]['enabled']
    restored.uninstallPlugin('sample-plugin')
    assert not (plugin_directory / 'sample-plugin').exists()
    assert restored.installedPlugins == []


def test_plugin_zip_rejects_path_traversal(tmp_path) -> None:
    """Never extract archive entries outside the managed staging directory."""
    archive = tmp_path / 'unsafe.zip'
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('..\\outside.txt', 'unsafe')

    with pytest.raises(PluginInstallError, match='unsafe path'):
        install_plugin_archive(str(archive), tmp_path / 'plugins')


def test_plugin_zip_cannot_replace_a_registered_plugin(tmp_path) -> None:
    """Protect bundled and package plugin IDs from user-archive replacement."""
    with pytest.raises(PluginInstallError, match='conflicts'):
        install_plugin_archive(
            str(_plugin_zip(tmp_path)),
            tmp_path / 'plugins',
            reserved_ids={'sample-plugin'},
        )
