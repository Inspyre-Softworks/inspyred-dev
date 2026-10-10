"""System-tray lifecycle for the desktop application.

Author: Taylor B. | Inspyre-Softworks.
"""

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QWindow
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from inspyred_dev.gui.quick_capture import QuickCaptureController


class SystemTrayController(QObject):
    """Keep the inbox available from the operating-system tray."""

    availableChanged = Signal()

    def __init__(
        self,
        app: QApplication,
        icon: QIcon,
        quick_capture: QuickCaptureController,
    ) -> None:
        """Create the tray icon and its actions.

        Parameters
        ----------
        app : QApplication
            Running desktop application.
        icon : QIcon
            Application icon shared with the window and tray.
        quick_capture : QuickCaptureController
            Controller invoked by the tray's quick-capture action.
        """
        super().__init__()
        self._app = app
        self._quick_capture = quick_capture
        self._window: QWindow | None = None
        self._available = QSystemTrayIcon.isSystemTrayAvailable()

        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip('Inspyred Dev')

        self._menu = QMenu()
        self._open_action = QAction('Open Inbox', self)
        self._capture_action = QAction('Quick Capture', self)
        self._quit_action = QAction('Quit', self)

        self._open_action.triggered.connect(self.showWindow)
        self._capture_action.triggered.connect(self._quick_capture.requestCapture)
        self._quit_action.triggered.connect(self.quit)

        self._menu.addAction(self._open_action)
        self._menu.addAction(self._capture_action)
        self._menu.addSeparator()
        self._menu.addAction(self._quit_action)
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._handle_activation)

        # Closing the last window should end the process when no tray exists.
        # Otherwise, closing the inbox leaves capture available in the tray.
        app.setQuitOnLastWindowClosed(not self._available)
        if self._available:
            self._tray.show()

    @Property(bool, notify=availableChanged)
    def available(self) -> bool:
        """Return whether the desktop exposes a usable system tray."""
        return self._available

    def setWindow(self, window: QWindow) -> None:  # noqa: N802
        """Attach the QML application window after it has been created.

        Parameters
        ----------
        window : QWindow
            Root QML window controlled by the tray actions.
        """
        self._window = window

    @Slot()
    def showWindow(self) -> None:  # noqa: N802
        """Restore and activate the observation inbox."""
        if self._window is None:
            return
        self._window.showNormal()
        self._window.raise_()
        self._window.requestActivate()

    @Slot(result=bool)
    def handleWindowClose(self) -> bool:  # noqa: N802
        """Hide the inbox when tray operation is available.

        Returns
        -------
        bool
            ``True`` when QML should cancel the close event because the window
            was hidden to the tray.
        """
        if not self._available or self._window is None:
            return False
        self._window.hide()
        return True

    @Slot()
    def quit(self) -> None:
        """Remove the tray icon and explicitly exit the application."""
        self._tray.hide()
        self._app.quit()

    @Slot(QSystemTrayIcon.ActivationReason)
    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.showWindow()
