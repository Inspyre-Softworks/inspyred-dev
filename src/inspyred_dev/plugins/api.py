"""Public contracts implemented by Inspyred Dev plugins.

Author: Taylor B. | Inspyre-Softworks.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from PySide6.QtCore import QObject


@dataclass(frozen=True)
class PluginMetadata:
    """Describe a plugin without activating it."""

    plugin_id: str
    name: str
    version: str


@dataclass(frozen=True)
class PluginServices:
    """Application-owned services available during plugin activation."""

    settings: QObject
    projects: QObject
    observations: QObject


@dataclass(frozen=True)
class PluginUiExtension:
    """Place a plugin-owned QML component in a named application slot."""

    slot: str
    source: Path


@dataclass(frozen=True)
class PluginContribution:
    """Objects and resources a plugin contributes to the application."""

    qml_context: Mapping[str, QObject] = field(default_factory=dict)
    qml_import_paths: tuple[Path, ...] = ()
    ui_extensions: tuple[PluginUiExtension, ...] = ()


@runtime_checkable
class ApplicationPlugin(Protocol):
    """Runtime contract for an Inspyred Dev plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return stable identity and display information for the plugin."""

    def activate(self, services: PluginServices) -> PluginContribution:
        """Create the plugin's application contributions."""

    def deactivate(self) -> None:
        """Release resources created during activation."""
