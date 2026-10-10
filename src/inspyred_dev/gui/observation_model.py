"""Qt model binding for observations.

Author: Taylor B. | Inspyre-Softworks.
"""

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)

from inspyred_dev.core.models import Observation, ObservationType, Priority
from inspyred_dev.gui.projects import ALL_PROJECTS, ProjectContext
from inspyred_dev.services.observation_store import ObservationStore


class ObservationListModel(QAbstractListModel):
    """Expose local observations to QML."""

    countChanged = Signal()

    IdRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = IdRole + 1
    DetailsRole = TitleRole + 1
    KindRole = DetailsRole + 1
    PriorityRole = KindRole + 1
    AreaRole = PriorityRole + 1
    StatusRole = AreaRole + 1
    CreatedAtRole = StatusRole + 1
    ScreenshotPathRole = CreatedAtRole + 1
    ScreenshotUrlRole = ScreenshotPathRole + 1
    ProjectRole = ScreenshotUrlRole + 1

    def __init__(self, store: ObservationStore, projects: ProjectContext) -> None:
        """Initialize the model from persisted observations.

        Parameters
        ----------
        store : ObservationStore
            Persistence service used to load and add observations.
        """
        super().__init__()
        self._store = store
        self._projects = projects
        self._items = store.list_all(self._project_filter())
        projects.activeProjectChanged.connect(self._reload)

    def _project_filter(self) -> str | None:
        if self._projects.activeProject == ALL_PROJECTS:
            return None
        return self._projects.activeProject

    @Slot()
    def _reload(self) -> None:
        self.beginResetModel()
        self._items = self._store.list_all(self._project_filter())
        self.endResetModel()
        self.countChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        """Return the number of locally captured observations."""
        return len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:
        """Return the role names exposed to QML delegates.

        Returns
        -------
        dict[int, QByteArray]
            Mapping from Qt role numbers to QML-facing names.
        """
        return {
            self.IdRole: QByteArray(b'observationId'),
            self.TitleRole: QByteArray(b'title'),
            self.DetailsRole: QByteArray(b'details'),
            self.KindRole: QByteArray(b'kind'),
            self.PriorityRole: QByteArray(b'priority'),
            self.AreaRole: QByteArray(b'area'),
            self.StatusRole: QByteArray(b'status'),
            self.CreatedAtRole: QByteArray(b'createdAt'),
            self.ScreenshotPathRole: QByteArray(b'screenshotPath'),
            self.ScreenshotUrlRole: QByteArray(b'screenshotUrl'),
            self.ProjectRole: QByteArray(b'project'),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows for a model index.

        Parameters
        ----------
        parent : QModelIndex
            Parent index supplied by Qt. A list model has rows only at its root.

        Returns
        -------
        int
            The number of observations for the root index, otherwise ``0``.
        """
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return the value associated with a role for an observation.

        Parameters
        ----------
        index : QModelIndex
            Index of the requested observation.
        role : int
            Qt role identifying the requested field.

        Returns
        -------
        object | None
            The requested field value, or ``None`` for an invalid index or
            unsupported role.
        """
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None

        item = self._items[index.row()]
        values = {
            self.IdRole: item.id,
            self.TitleRole: item.title,
            self.DetailsRole: item.details,
            self.KindRole: item.kind.value,
            self.PriorityRole: item.priority.value,
            self.AreaRole: item.area,
            self.StatusRole: item.status.value,
            self.ScreenshotPathRole: item.screenshot_path,
            self.ScreenshotUrlRole: (
                QUrl.fromLocalFile(item.screenshot_path).toString()
                if item.screenshot_path
                else ''
            ),
            self.ProjectRole: item.project,
            self.CreatedAtRole: item.created_at.astimezone().strftime('%b %d, %Y · %I:%M %p'),
        }
        return values.get(role)

    @Slot(str, str, str, str, str, str, result=bool)
    def addObservation(
        self,
        title: str,
        kind: str,
        priority: str,
        area: str,
        details: str,
        screenshot_path: str,
    ) -> bool:  # noqa: N802
        """Validate, persist, and prepend an observation supplied by QML.

        Parameters
        ----------
        title : str
            Required observation summary.
        kind : str
            Value from :class:`~inspyred_dev.core.models.ObservationType`.
        priority : str
            Value from :class:`~inspyred_dev.core.models.Priority`.
        area : str
            Optional product or code area.
        details : str
            Optional supporting context.
        screenshot_path : str
            Optional path to a captured screenshot.

        Returns
        -------
        bool
            ``True`` when the observation is saved; ``False`` when the title
            is empty.

        Raises
        ------
        ValueError
            If ``kind`` or ``priority`` is not a supported enum value.
        """
        title = title.strip()
        if not title:
            return False

        observation = self._store.add(
            Observation(
                title=title,
                details=details.strip(),
                kind=ObservationType(kind),
                priority=Priority(priority),
                area=area.strip(),
                project=self._projects.captureProject,
                screenshot_path=screenshot_path.strip(),
            )
        )

        self.beginInsertRows(QModelIndex(), 0, 0)
        self._items.insert(0, observation)
        self.endInsertRows()
        self.countChanged.emit()
        return True
