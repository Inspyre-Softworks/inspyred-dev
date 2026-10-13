"""Qt application bootstrap.

Author: Taylor B. | Inspyre-Softworks.
"""

from pathlib import Path
import sys
from typing import cast

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from inspyred_dev import __version__
from inspyred_dev.gui.help_registry import HelpRegistry
from inspyred_dev.gui.observation_model import ObservationListModel
from inspyred_dev.gui.projects import ProjectContext
from inspyred_dev.gui.quick_capture import QuickCaptureController
from inspyred_dev.gui.settings import AppSettings
from inspyred_dev.gui.system_tray import SystemTrayController
from inspyred_dev.gui.theme import ThemeController
from inspyred_dev.plugins import PluginRegistry, PluginServices
from inspyred_dev.plugins.github import GitHubPlugin
from inspyred_dev.services.observation_store import ObservationStore


def _set_windows_app_user_model_id() -> None:
    """Give Windows a stable identity for taskbar grouping and icon selection."""
    if sys.platform != 'win32':
        return

    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore[attr-defined]
        'InspyreSoftworks.InspyredDev'
    )


def run() -> int:
    """Create and execute the desktop application.

    Returns
    -------
    int
        The Qt event loop's process exit code, or ``1`` when the QML root
        object cannot be created.
    """
    _set_windows_app_user_model_id()
    QQuickStyle.setStyle('Basic')
    app = QApplication(sys.argv)
    app.setApplicationName('Inspyred Dev')
    app.setApplicationVersion(__version__)
    app.setOrganizationName('Inspyre-Softworks')

    qml_root = Path(__file__).resolve().parent.parent / 'qml'
    app_icon = QIcon(str(qml_root / 'assets' / 'neon-id-spark-app-icon.png'))
    app.setWindowIcon(app_icon)

    settings = AppSettings()
    theme = ThemeController(settings)
    help_registry = HelpRegistry()
    projects = ProjectContext()
    observations = ObservationListModel(ObservationStore(), projects)
    quick_capture = QuickCaptureController(app, settings)
    system_tray = SystemTrayController(app, app_icon, quick_capture)
    plugins = PluginRegistry([GitHubPlugin()])
    plugins.discover()
    plugins.activate_all(PluginServices(settings, projects, observations))

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty('AppSettings', settings)
    context.setContextProperty('Theme', theme)
    context.setContextProperty('HelpRegistry', help_registry)
    context.setContextProperty('Plugins', plugins)
    context.setContextProperty('Observations', observations)
    context.setContextProperty('Projects', projects)
    context.setContextProperty('QuickCapture', quick_capture)
    context.setContextProperty('SystemTray', system_tray)
    for name, value in plugins.qml_context.items():
        context.setContextProperty(name, value)

    engine.addImportPath(str(qml_root))
    for import_path in plugins.qml_import_paths:
        engine.addImportPath(str(import_path))
    engine.load(QUrl.fromLocalFile(str(qml_root / 'Main.qml')))

    if not engine.rootObjects():
        plugins.deactivate_all()
        return 1
    root_window = cast(QWindow, engine.rootObjects()[0])
    root_window.setIcon(app.windowIcon())
    system_tray.setWindow(root_window)
    exit_code = app.exec()

    # Context properties are borrowed references. Destroy the QML object tree while
    # its Python-backed context objects are still alive so shutdown does not briefly
    # re-evaluate bindings against null Theme/Settings/model objects.
    del context
    del engine
    plugins.deactivate_all()
    return exit_code
