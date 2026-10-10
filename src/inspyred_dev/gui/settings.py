"""Persistent application appearance settings.

Author: Taylor B. | Inspyre-Softworks.
"""

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot


class AppSettings(QObject):
    """Persist application preferences and expose them to QML.

    Notes
    -----
    Values are stored through :class:`PySide6.QtCore.QSettings`, which selects
    the platform-native settings backend.
    """

    themeModeChanged = Signal()
    labelModeChanged = Signal()
    globalCaptureEnabledChanged = Signal()
    captureScreenshotsChanged = Signal()

    def __init__(self) -> None:
        """Load application settings from the platform-native settings store."""
        super().__init__()
        self._settings = QSettings('Inspyre-Softworks', 'Inspyred Dev')
        self._theme_mode = str(self._settings.value('appearance/themeMode', 'dark'))
        self._label_mode = str(self._settings.value('appearance/labelMode', 'icons_text'))
        self._global_capture_enabled = bool(
            self._settings.value('capture/globalShortcutEnabled', True, type=bool)
        )
        self._capture_screenshots = bool(
            self._settings.value('capture/activeWindowScreenshot', True, type=bool)
        )

    @Property(str, notify=themeModeChanged)
    def themeMode(self) -> str:  # noqa: N802 - Qt property naming
        """Return the configured color theme mode."""
        return self._theme_mode

    @themeMode.setter
    def themeMode(self, value: str) -> None:  # noqa: N802
        """Persist a valid color theme mode and notify QML.

        Parameters
        ----------
        value : str
            One of ``system``, ``light``, or ``dark``.
        """
        if value not in {'system', 'light', 'dark'} or value == self._theme_mode:
            return
        self._theme_mode = value
        self._settings.setValue('appearance/themeMode', value)
        self.themeModeChanged.emit()

    @Property(str, notify=labelModeChanged)
    def labelMode(self) -> str:  # noqa: N802
        """Return the configured icon-label presentation mode."""
        return self._label_mode

    @labelMode.setter
    def labelMode(self, value: str) -> None:  # noqa: N802
        """Persist a valid icon-label mode and notify QML.

        Parameters
        ----------
        value : str
            Either ``icons_only`` or ``icons_text``.
        """
        if value not in {'icons_only', 'icons_text'} or value == self._label_mode:
            return
        self._label_mode = value
        self._settings.setValue('appearance/labelMode', value)
        self.labelModeChanged.emit()

    @Property(bool, notify=labelModeChanged)
    def labelsEnabled(self) -> bool:  # noqa: N802
        """Return whether persistent text labels are enabled."""
        return self._label_mode == 'icons_text'

    @Property(bool, notify=globalCaptureEnabledChanged)
    def globalCaptureEnabled(self) -> bool:  # noqa: N802
        """Return whether the global quick-capture shortcut is enabled."""
        return self._global_capture_enabled

    @globalCaptureEnabled.setter
    def globalCaptureEnabled(self, value: bool) -> None:  # noqa: N802
        """Persist the global quick-capture preference.

        Parameters
        ----------
        value : bool
            Whether the native global shortcut should be registered.
        """
        value = bool(value)
        if value == self._global_capture_enabled:
            return
        self._global_capture_enabled = value
        self._settings.setValue('capture/globalShortcutEnabled', value)
        self.globalCaptureEnabledChanged.emit()

    @Property(bool, notify=captureScreenshotsChanged)
    def captureScreenshots(self) -> bool:  # noqa: N802
        """Return whether quick capture should include the active window."""
        return self._capture_screenshots

    @captureScreenshots.setter
    def captureScreenshots(self, value: bool) -> None:  # noqa: N802
        """Persist the active-window screenshot preference.

        Parameters
        ----------
        value : bool
            Whether quick capture should take an active-window screenshot.
        """
        value = bool(value)
        if value == self._capture_screenshots:
            return
        self._capture_screenshots = value
        self._settings.setValue('capture/activeWindowScreenshot', value)
        self.captureScreenshotsChanged.emit()

    @Slot(str)
    def setThemeMode(self, value: str) -> None:  # noqa: N802
        """Set the theme mode from QML."""
        self.themeMode = value

    @Slot(str)
    def setLabelMode(self, value: str) -> None:  # noqa: N802
        """Set the icon-label mode from QML."""
        self.labelMode = value

    @Slot(bool)
    def setGlobalCaptureEnabled(self, value: bool) -> None:  # noqa: N802
        """Enable or disable global quick capture from QML."""
        self.globalCaptureEnabled = value

    @Slot(bool)
    def setCaptureScreenshots(self, value: bool) -> None:  # noqa: N802
        """Enable or disable active-window screenshots from QML."""
        self.captureScreenshots = value
