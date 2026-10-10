"""Global quick-capture shortcut and active-window screenshot support.

Author: Taylor B. | Inspyre-Softworks.
"""

import ctypes
import sys
from ctypes import wintypes
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from platformdirs import user_data_dir
from PySide6.QtCore import QPoint, Property, QAbstractNativeEventFilter, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from inspyred_dev.gui.settings import AppSettings


WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
VK_N = 0x4E
HOTKEY_ID = 0x1D51


def _discard_managed_screenshot(screenshot_path: str, capture_dir: Path) -> None:
    """Delete a screenshot only when it belongs to the managed capture directory."""
    if not screenshot_path:
        return

    try:
        candidate = Path(screenshot_path).resolve()
        capture_root = capture_dir.resolve()
        if candidate.is_relative_to(capture_root):
            candidate.unlink(missing_ok=True)
    except OSError:
        pass


class _WindowsHotkeyFilter(QAbstractNativeEventFilter):
    """Forward the registered Windows hotkey into the Qt object graph."""

    def __init__(self, callback) -> None:
        """Initialize the native event filter.

        Parameters
        ----------
        callback : Callable[[], None]
            Function invoked when the registered Windows hotkey is pressed.
        """
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message):  # noqa: N802
        """Handle a native Windows hotkey event.

        Parameters
        ----------
        event_type : QByteArray
            Native event category supplied by Qt.
        message : int
            Address of the native Windows message.

        Returns
        -------
        tuple[bool, int]
            A handled flag and native result value.
        """
        event_name = bytes(event_type).decode(errors='ignore')
        if event_name not in {'windows_generic_MSG', 'windows_dispatcher_MSG'}:
            return False, 0

        native_message = wintypes.MSG.from_address(int(message))
        if native_message.message == WM_HOTKEY and native_message.wParam == HOTKEY_ID:
            self._callback()
            return True, 0
        return False, 0


class QuickCaptureController(QObject):
    """Own the global shortcut and prepare screenshots for the capture UI."""

    captureRequested = Signal(str, str)
    hotkeyRegisteredChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, app: QGuiApplication, settings: AppSettings) -> None:
        """Register capture behavior with the application.

        Parameters
        ----------
        app : QGuiApplication
            Running Qt application that receives native events.
        settings : AppSettings
            Persisted settings controlling shortcut and screenshot behavior.
        """
        super().__init__()
        self._app = app
        self._settings = settings
        self._hotkey_registered = False
        self._last_error = ''
        self._filter = _WindowsHotkeyFilter(self._handle_hotkey)
        self._capture_dir = Path(user_data_dir('Inspyred Dev', 'Inspyre-Softworks')) / 'captures'

        app.installNativeEventFilter(self._filter)
        app.aboutToQuit.connect(self.close)
        settings.globalCaptureEnabledChanged.connect(self._sync_registration)
        self._sync_registration()

    @Property(bool, notify=hotkeyRegisteredChanged)
    def hotkeyRegistered(self) -> bool:  # noqa: N802
        """Return whether the global quick-capture hotkey is registered."""
        return self._hotkey_registered

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:  # noqa: N802
        """Return the latest user-facing capture error, if any."""
        return self._last_error

    def _set_registered(self, value: bool) -> None:
        if value == self._hotkey_registered:
            return
        self._hotkey_registered = value
        self.hotkeyRegisteredChanged.emit()

    def _set_error(self, value: str) -> None:
        if value == self._last_error:
            return
        self._last_error = value
        self.lastErrorChanged.emit()

    @Slot()
    def _sync_registration(self) -> None:
        if sys.platform != 'win32':
            self._set_registered(False)
            self._set_error('Global capture shortcuts are currently available on Windows only.')
            return

        user32 = ctypes.windll.user32
        if self._hotkey_registered:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            self._set_registered(False)

        if not self._settings.globalCaptureEnabled:
            self._set_error('')
            return

        registered = bool(
            user32.RegisterHotKey(
                None,
                HOTKEY_ID,
                MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT,
                VK_N,
            )
        )
        self._set_registered(registered)
        self._set_error(
            '' if registered else 'Ctrl+Shift+N is already in use by another application.'
        )

    def _capture_active_window(self) -> tuple[str, str]:
        if sys.platform != 'win32':
            return '', ''

        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            raise RuntimeError('The active window could not be identified.')

        window_rect = wintypes.RECT()
        if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(window_rect)):
            center = QPoint(
                (window_rect.left + window_rect.right) // 2,
                (window_rect.top + window_rect.bottom) // 2,
            )
            screen = QGuiApplication.screenAt(center)
        else:
            screen = None
        screen = screen or QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError('The active window could not be identified.')

        pixmap = screen.grabWindow(hwnd)
        if pixmap.isNull():
            raise RuntimeError('The active window could not be captured.')

        self._capture_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime('%Y%m%d-%H%M%S-%f')
        path = self._capture_dir / f'active-window-{stamp}-{uuid4().hex[:8]}.png'
        if not pixmap.save(str(path), 'PNG'):
            raise RuntimeError('The active-window screenshot could not be saved.')
        return str(path), QUrl.fromLocalFile(str(path)).toString()

    def _handle_hotkey(self) -> None:
        self.requestCapture()

    @Slot()
    def requestCapture(self) -> None:  # noqa: N802
        """Capture optional window context and open the quick-capture UI."""
        screenshot_path = ''
        screenshot_url = ''
        if self._settings.captureScreenshots:
            try:
                screenshot_path, screenshot_url = self._capture_active_window()
                self._set_error('')
            except RuntimeError as error:
                self._set_error(str(error))

        self.captureRequested.emit(screenshot_path, screenshot_url)

    @Slot(str)
    def discardScreenshot(self, screenshot_path: str) -> None:  # noqa: N802
        """Delete an unused screenshot from the managed capture directory.

        Paths outside the capture directory are ignored.

        Parameters
        ----------
        screenshot_path : str
            Candidate screenshot path supplied by QML.
        """
        _discard_managed_screenshot(screenshot_path, self._capture_dir)

    @Slot()
    def close(self) -> None:
        """Release the native hotkey before the application exits."""
        if sys.platform == 'win32' and self._hotkey_registered:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
            self._set_registered(False)
