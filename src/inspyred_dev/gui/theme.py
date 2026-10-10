"""Theme controller exposed to QML.

Author: Taylor B. | Inspyre-Softworks.
"""

from PySide6.QtCore import Property, QObject, Signal
from PySide6.QtGui import QColor, QGuiApplication, Qt

from inspyred_dev.gui.settings import AppSettings


class ThemeController(QObject):
    """Resolve application colors from system/light/dark preferences."""

    changed = Signal()

    LIGHT = {
        'background': '#EAF5FF',
        'backgroundAlt': '#DCEBFF',
        'surface': '#F8FBFF',
        'surfaceAlt': '#E7F1FF',
        'surfaceRaised': '#FFFFFF',
        'textPrimary': '#07152F',
        'textSecondary': '#526581',
        'border': '#A9C7EE',
        'borderStrong': '#448DFF',
        'accent': '#087DFF',
        'accentHover': '#006BE0',
        'cyan': '#00BFD8',
        'violet': '#8C4DFF',
        'success': '#00A88F',
        'danger': '#D33E68',
        'glow': '#420087FF',
        'shadow': '#2B001C4A',
    }
    DARK = {
        'background': '#02091C',
        'backgroundAlt': '#06163A',
        'surface': '#07152F',
        'surfaceAlt': '#0B214A',
        'surfaceRaised': '#0A1D42',
        'textPrimary': '#F7FAFF',
        'textSecondary': '#A9BBDB',
        'border': '#174A91',
        'borderStrong': '#0788FF',
        'accent': '#087DFF',
        'accentHover': '#00B7FF',
        'cyan': '#11E4F2',
        'violet': '#A66CFF',
        'success': '#17D9B0',
        'danger': '#FF527D',
        'glow': '#870087FF',
        'shadow': '#B0000208',
    }

    def __init__(self, settings: AppSettings) -> None:
        """Initialize the controller and listen for palette changes.

        Parameters
        ----------
        settings : AppSettings
            Preferences used to resolve the effective theme.
        """
        super().__init__()
        self._settings = settings
        settings.themeModeChanged.connect(self.changed.emit)

        hints = QGuiApplication.styleHints()
        if hasattr(hints, 'colorSchemeChanged'):
            hints.colorSchemeChanged.connect(self.changed.emit)

    def _is_dark(self) -> bool:
        mode = self._settings.themeMode
        if mode == 'dark':
            return True
        if mode == 'light':
            return False
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark

    def _color(self, name: str) -> QColor:
        palette = self.DARK if self._is_dark() else self.LIGHT
        return QColor(palette[name])

    @Property(bool, notify=changed)
    def dark(self) -> bool:
        """Return whether the effective theme is dark."""
        return self._is_dark()

    @Property(QColor, notify=changed)
    def background(self) -> QColor:
        """Return the primary background color."""
        return self._color('background')

    @Property(QColor, notify=changed)
    def surface(self) -> QColor:
        """Return the primary surface color."""
        return self._color('surface')

    @Property(QColor, notify=changed)
    def surfaceAlt(self) -> QColor:  # noqa: N802
        """Return the alternate surface color."""
        return self._color('surfaceAlt')

    @Property(QColor, notify=changed)
    def backgroundAlt(self) -> QColor:  # noqa: N802
        """Return the alternate background color."""
        return self._color('backgroundAlt')

    @Property(QColor, notify=changed)
    def surfaceRaised(self) -> QColor:  # noqa: N802
        """Return the raised-surface color."""
        return self._color('surfaceRaised')

    @Property(QColor, notify=changed)
    def textPrimary(self) -> QColor:  # noqa: N802
        """Return the primary text color."""
        return self._color('textPrimary')

    @Property(QColor, notify=changed)
    def textSecondary(self) -> QColor:  # noqa: N802
        """Return the secondary text color."""
        return self._color('textSecondary')

    @Property(QColor, notify=changed)
    def border(self) -> QColor:
        """Return the standard border color."""
        return self._color('border')

    @Property(QColor, notify=changed)
    def borderStrong(self) -> QColor:  # noqa: N802
        """Return the emphasized border color."""
        return self._color('borderStrong')

    @Property(QColor, notify=changed)
    def accent(self) -> QColor:
        """Return the primary accent color."""
        return self._color('accent')

    @Property(QColor, notify=changed)
    def accentHover(self) -> QColor:  # noqa: N802
        """Return the accent color for hovered controls."""
        return self._color('accentHover')

    @Property(QColor, notify=changed)
    def cyan(self) -> QColor:
        """Return the cyan highlight color."""
        return self._color('cyan')

    @Property(QColor, notify=changed)
    def violet(self) -> QColor:
        """Return the violet highlight color."""
        return self._color('violet')

    @Property(QColor, notify=changed)
    def success(self) -> QColor:
        """Return the success-state color."""
        return self._color('success')

    @Property(QColor, notify=changed)
    def danger(self) -> QColor:
        """Return the danger-state color."""
        return self._color('danger')

    @Property(QColor, notify=changed)
    def shadow(self) -> QColor:
        """Return the shadow color."""
        return self._color('shadow')

    @Property(QColor, notify=changed)
    def glow(self) -> QColor:
        """Return the translucent accent glow color."""
        return self._color('glow')
