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

from inspyred_dev.core.models import Observation, ObservationStatus, ObservationType, Priority
from inspyred_dev.gui.projects import ALL_PROJECTS, ProjectContext
from inspyred_dev.services.observation_store import ObservationStore


class ObservationListModel(QAbstractListModel):
    """Expose local observations to QML."""

    countChanged = Signal()
    selectionChanged = Signal()
    viewStatusChanged = Signal()

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
    GithubIssueNumberRole = ProjectRole + 1
    GithubIssueUrlRole = GithubIssueNumberRole + 1
    SelectedRole = GithubIssueUrlRole + 1

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
        self._view_status = ObservationStatus.INBOX
        self._items = store.list_all(self._project_filter(), self._view_status)
        self._selected_ids: set[int] = set()
        projects.projectRenamed.connect(self._rename_project)
        projects.activeProjectChanged.connect(self._reload)

    def _project_filter(self) -> str | None:
        if self._projects.activeProject == ALL_PROJECTS:
            return None
        return self._projects.activeProject

    @Slot()
    def _reload(self) -> None:
        self.beginResetModel()
        self._items = self._store.list_all(self._project_filter(), self._view_status)
        self._selected_ids.clear()
        self.endResetModel()
        self.countChanged.emit()
        self.selectionChanged.emit()

    @Slot(str, str)
    def _rename_project(self, old_name: str, new_name: str) -> None:
        """Keep persisted observations attached when their project is renamed."""
        self._store.rename_project(old_name, new_name)
        self._reload()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        """Return the number of locally captured observations."""
        return len(self._items)

    @Property(str, notify=viewStatusChanged)
    def viewStatus(self) -> str:  # noqa: N802
        """Return the workflow status currently displayed by the inbox."""
        return self._view_status.value

    @Property(bool, notify=viewStatusChanged)
    def showingShelved(self) -> bool:  # noqa: N802
        """Return whether the model is displaying shelved observations."""
        return self._view_status is ObservationStatus.SHELVED

    @Slot(str)
    def setViewStatus(self, status: str) -> None:  # noqa: N802
        """Switch between active inbox and shelved observations."""
        try:
            requested = ObservationStatus(status)
        except ValueError:
            return
        if requested not in {ObservationStatus.INBOX, ObservationStatus.SHELVED}:
            return
        if requested is self._view_status:
            return
        self._view_status = requested
        self.viewStatusChanged.emit()
        self._reload()

    @Property(int, notify=selectionChanged)
    def selectedCount(self) -> int:  # noqa: N802
        """Return the number of observations selected for a batch action."""
        return len(self._selected_ids)

    @Property(int, notify=selectionChanged)
    def selectedRepositoryCount(self) -> int:  # noqa: N802
        """Return the number of GitHub repositories represented by the selection."""
        return len(
            {
                self._projects.githubRepositoryUrl(item.project).casefold()
                for item in self._selected_observations()
                if self._projects.githubRepositoryUrl(item.project)
            }
        )

    @Property(str, notify=selectionChanged)
    def selectedRepositoryUrl(self) -> str:  # noqa: N802
        """Return the single repository URL that owns the current selection."""
        observations = self._selected_observations()
        if not observations:
            return ''
        return self._projects.githubRepositoryUrl(observations[0].project)

    @Property(str, notify=selectionChanged)
    def selectedProjectName(self) -> str:  # noqa: N802
        """Return the project shared by the selected observations."""
        observations = self._selected_observations()
        return observations[0].project if observations else ''

    @Property(bool, notify=selectionChanged)
    def selectedGithubIssueEligible(self) -> bool:  # noqa: N802
        """Return whether the selected notes can become issues in their repository."""
        observations = self._selected_observations()
        if not observations or any(item.github_issue_url for item in observations):
            return False
        repository_url = self._projects.githubRepositoryUrl(observations[0].project)
        return bool(repository_url)

    @Property(str, notify=selectionChanged)
    def githubIssueSelectionError(self) -> str:  # noqa: N802
        """Explain why the current project selection cannot create issues."""
        observations = self._selected_observations()
        if not observations or self.selectedGithubIssueEligible:
            return ''
        if not self._projects.githubRepositoryUrl(observations[0].project):
            return 'This project is not connected to a GitHub repository.'
        return 'Notes already linked to GitHub issues cannot create another issue.'

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
            self.GithubIssueNumberRole: QByteArray(b'githubIssueNumber'),
            self.GithubIssueUrlRole: QByteArray(b'githubIssueUrl'),
            self.SelectedRole: QByteArray(b'selected'),
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
                QUrl.fromLocalFile(item.screenshot_path).toString() if item.screenshot_path else ''
            ),
            self.ProjectRole: item.project,
            self.GithubIssueNumberRole: item.github_issue_number,
            self.GithubIssueUrlRole: item.github_issue_url,
            self.SelectedRole: item.id in self._selected_ids,
            self.CreatedAtRole: item.created_at.astimezone().strftime('%b %d, %Y · %I:%M %p'),
        }
        return values.get(role)

    def _selected_observations(self) -> list[Observation]:
        return [item for item in self._items if item.id in self._selected_ids]

    @Slot(int)
    def toggleSelection(self, observation_id: int) -> None:  # noqa: N802
        """Add or remove an observation while keeping selection project-scoped."""
        row = next(
            (index for index, item in enumerate(self._items) if item.id == observation_id),
            None,
        )
        if row is None:
            return
        candidate_project = self._items[row].project
        if (
            self._selected_ids
            and observation_id not in self._selected_ids
            and candidate_project.casefold() != self.selectedProjectName.casefold()
        ):
            return
        if observation_id in self._selected_ids:
            self._selected_ids.remove(observation_id)
        else:
            self._selected_ids.add(observation_id)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [self.SelectedRole])
        self.selectionChanged.emit()

    @Slot()
    def selectAll(self) -> None:  # noqa: N802
        """Select every observation when the current view contains one project."""
        projects = {item.project.casefold() for item in self._items}
        if len(projects) > 1:
            return
        selected_ids = {item.id for item in self._items if item.id is not None}
        if selected_ids == self._selected_ids:
            return
        self._selected_ids = selected_ids
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
                [self.SelectedRole],
            )
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:  # noqa: N802
        """Clear all observations selected for batch actions."""
        if not self._selected_ids:
            return
        self._selected_ids.clear()
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
                [self.SelectedRole],
            )
        self.selectionChanged.emit()

    def _row_for_id(self, observation_id: int) -> int | None:
        return next(
            (index for index, item in enumerate(self._items) if item.id == observation_id),
            None,
        )

    def _remove_row(self, row: int) -> None:
        observation_id = self._items[row].id
        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row)
        self.endRemoveRows()
        if observation_id in self._selected_ids:
            self._selected_ids.remove(observation_id)
            self.selectionChanged.emit()
        self.countChanged.emit()

    @Slot(int, result=bool)
    def toggleShelved(self, observation_id: int) -> bool:  # noqa: N802
        """Shelve an inbox note or restore a shelved note to the inbox."""
        row = self._row_for_id(observation_id)
        if row is None:
            return False
        status = (
            ObservationStatus.INBOX
            if self._items[row].status is ObservationStatus.SHELVED
            else ObservationStatus.SHELVED
        )
        if not self._store.update_status(observation_id, status):
            return False
        self._remove_row(row)
        return True

    def _change_priority(self, observation_id: int, offset: int) -> bool:
        row = self._row_for_id(observation_id)
        if row is None:
            return False
        priorities = [Priority.P1, Priority.P2, Priority.P3]
        current_index = priorities.index(self._items[row].priority)
        next_index = max(0, min(len(priorities) - 1, current_index + offset))
        if next_index == current_index:
            return False
        priority = priorities[next_index]
        if not self._store.update_priority(observation_id, priority):
            return False
        self._items[row] = self._items[row].model_copy(update={'priority': priority})
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [self.PriorityRole])
        return True

    @Slot(int, result=bool)
    def increasePriority(self, observation_id: int) -> bool:  # noqa: N802
        """Move a note one step toward P1."""
        return self._change_priority(observation_id, -1)

    @Slot(int, result=bool)
    def decreasePriority(self, observation_id: int) -> bool:  # noqa: N802
        """Move a note one step toward P3."""
        return self._change_priority(observation_id, 1)

    @Slot(int, result=bool)
    def deleteObservation(self, observation_id: int) -> bool:  # noqa: N802
        """Permanently delete one note from local storage and the visible model."""
        row = self._row_for_id(observation_id)
        if row is None or not self._store.delete(observation_id):
            return False
        self._remove_row(row)
        return True

    @staticmethod
    def _observation_markdown(observation: Observation, include_heading: bool = True) -> str:
        context = observation.details.strip() or '_No additional context was captured._'
        area = observation.area.strip() or 'Not specified'
        heading = f'### {observation.title}\n\n' if include_heading else ''
        return (
            f'{heading}{context}\n\n'
            f'- **Type:** {observation.kind.value}\n'
            f'- **Priority:** {observation.priority.value}\n'
            f'- **Area:** {area}'
        )

    def _issue_request(
        self,
        observations: list[Observation],
        title: str,
    ) -> dict[str, object]:
        repository_url = self._projects.githubRepositoryUrl(observations[0].project)
        if len(observations) == 1:
            body = self._observation_markdown(observations[0], include_heading=False)
        else:
            sections = [self._observation_markdown(observation) for observation in observations]
            body = '## Selected observations\n\n' + '\n\n---\n\n'.join(sections)
        body += '\n\n---\nCreated from Inspyred Dev observations.'
        return {
            'observation_ids': [observation.id for observation in observations],
            'repository_url': repository_url,
            'title': title,
            'body': body,
        }

    @Slot(str, str, result='QVariantList')
    def buildGithubIssueBatch(self, mode: str, keyword_text: str) -> list[dict[str, object]]:  # noqa: N802
        """Build issue requests for combined, keyword-grouped, or individual publishing."""
        observations = self._selected_observations()
        if not self.selectedGithubIssueEligible:
            return []
        if mode == 'individual':
            return [
                self._issue_request([observation], observation.title)
                for observation in observations
            ]
        if mode == 'one':
            title = (
                observations[0].title
                if len(observations) == 1
                else f'Address {len(observations)} selected observations'
            )
            return [self._issue_request(observations, title)]
        if mode != 'keywords':
            return []
        keywords = list(
            dict.fromkeys(keyword.strip() for keyword in keyword_text.split(',') if keyword.strip())
        )
        if not keywords:
            return []
        groups: dict[str, list[Observation]] = {keyword: [] for keyword in keywords}
        unmatched: list[Observation] = []
        for observation in observations:
            searchable = ' '.join(
                [
                    observation.title,
                    observation.details,
                    observation.area,
                    observation.kind.value,
                ]
            ).casefold()
            keyword = next(
                (candidate for candidate in keywords if candidate.casefold() in searchable),
                None,
            )
            if keyword is None:
                unmatched.append(observation)
            else:
                groups[keyword].append(observation)
        requests = [
            self._issue_request(group, f'{keyword}: {len(group)} selected observation(s)')
            for keyword, group in groups.items()
            if group
        ]
        if unmatched:
            requests.append(
                self._issue_request(
                    unmatched,
                    f'Other: {len(unmatched)} selected observation(s)',
                )
            )
        return requests

    def _ai_instruction(self, observations: list[Observation]) -> str:
        project = observations[0].project
        repository_url = self._projects.githubRepositoryUrl(project)
        if len(observations) == 1:
            observation = observations[0]
            context = observation.details.strip() or 'No additional context was captured.'
            area = observation.area.strip() or 'Not specified'
            return (
                f'# Coding instruction: {observation.title}\n\n'
                f'Project: {project}\n'
                f'Repository: {repository_url or "Local project"}\n\n'
                '## Objective\n'
                f'{observation.title}\n\n'
                '## Context\n'
                f'{context}\n\n'
                '## Classification\n'
                f'- Type: {observation.kind.value}\n'
                f'- Priority: {observation.priority.value}\n'
                f'- Area: {area}\n\n'
                '## Delivery requirements\n'
                '- Inspect the existing implementation before changing it.\n'
                '- Implement the smallest coherent change that satisfies the objective.\n'
                '- Preserve existing behavior outside the requested scope.\n'
                '- Add or update tests appropriate to the change.\n'
                '- Verify the result and summarize the files changed.'
            )
        sections = []
        for index, observation in enumerate(observations, start=1):
            context = observation.details.strip() or 'No additional context was captured.'
            area = observation.area.strip() or 'Not specified'
            sections.append(
                f'### {index}. {observation.title}\n'
                f'{context}\n\n'
                f'- Type: {observation.kind.value}\n'
                f'- Priority: {observation.priority.value}\n'
                f'- Area: {area}'
            )
        return (
            f'# Coding instruction: {len(observations)} selected observations\n\n'
            f'Project: {project}\n'
            f'Repository: {repository_url or "Local project"}\n\n'
            'Implement the following observations as one coherent change. Resolve shared '
            'concerns together, but preserve each stated outcome.\n\n'
            + '\n\n'.join(sections)
            + '\n\n## Delivery requirements\n'
            '- Inspect the existing implementation before changing it.\n'
            '- Keep the work scoped to these observations.\n'
            '- Add or update tests for each affected behavior.\n'
            '- Verify the complete change and summarize the files changed.'
        )

    @Slot(int, result=str)
    def aiInstructionForObservation(self, observation_id: int) -> str:  # noqa: N802
        """Create a copy-ready coding instruction for one observation."""
        observation = next(
            (item for item in self._items if item.id == observation_id),
            None,
        )
        return self._ai_instruction([observation]) if observation is not None else ''

    @Slot(str, result=str)
    def buildSelectedAiInstructions(self, mode: str) -> str:  # noqa: N802
        """Create one combined brief or separate briefs for selected observations."""
        observations = self._selected_observations()
        if not observations:
            return ''
        if mode == 'individual':
            return '\n\n---\n\n'.join(
                self._ai_instruction([observation]) for observation in observations
            )
        return self._ai_instruction(observations)

    @Slot(str)
    def copyText(self, value: str) -> None:  # noqa: N802
        """Copy generated text to the operating-system clipboard."""
        if value:
            from PySide6.QtGui import QGuiApplication

            QGuiApplication.clipboard().setText(value)

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

        if self._view_status is ObservationStatus.INBOX:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self._items.insert(0, observation)
            self.endInsertRows()
            self.countChanged.emit()
        return True

    @Slot(int, int, str)
    def linkGithubIssue(
        self,
        observation_id: int,
        issue_number: int,
        issue_url: str,
    ) -> None:
        """Persist and publish a GitHub issue created for an observation."""
        for row, observation in enumerate(self._items):
            if observation.id != observation_id:
                continue
            if not self._store.link_github_issue(observation_id, issue_number, issue_url):
                return
            self._items[row] = observation.model_copy(
                update={
                    'github_issue_number': issue_number,
                    'github_issue_url': issue_url,
                }
            )
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [
                    self.GithubIssueNumberRole,
                    self.GithubIssueUrlRole,
                    self.SelectedRole,
                ],
            )
            if observation_id in self._selected_ids:
                self._selected_ids.remove(observation_id)
                self.selectionChanged.emit()
            return
