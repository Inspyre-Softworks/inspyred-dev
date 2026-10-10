"""Persisted project selection exposed to QML.

Author: Taylor B. | Inspyre-Softworks.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Property, QObject, QSettings, QUrl, Signal, Slot


ALL_PROJECTS = 'All projects'
DEFAULT_PROJECT = 'Inspyred Dev'
MAX_PROJECT_NAME_LENGTH = 120
PROJECT_SOURCES = {'folder', 'github'}


@dataclass(frozen=True)
class ProjectRecord:
    """Describe a project and the workspace it represents."""

    name: str
    source: str
    location: str


class ProjectContext(QObject):
    """Own available workspace projects and the active inbox project."""

    projectsChanged = Signal()
    activeProjectChanged = Signal()

    def __init__(self, settings: QSettings | None = None) -> None:
        """Load the project catalog and active selection."""
        super().__init__()
        self._settings = settings or QSettings('Inspyre-Softworks', 'Inspyred Dev')
        self._projects = self._load_projects()
        stored_active = str(self._settings.value('projects/active', DEFAULT_PROJECT))
        active_record = self._find_project(stored_active)
        self._active_project = (
            ALL_PROJECTS
            if stored_active == ALL_PROJECTS
            else (active_record.name if active_record is not None else DEFAULT_PROJECT)
        )

    def _load_projects(self) -> list[ProjectRecord]:
        raw_records = self._settings.value('projects/records', '')
        records: list[ProjectRecord] = []
        if raw_records:
            try:
                values = json.loads(str(raw_records))
                records = [
                    ProjectRecord(
                        name=str(value['name']).strip(),
                        source=str(value.get('source', 'folder')).strip(),
                        location=str(value.get('location', '')).strip(),
                    )
                    for value in values
                    if isinstance(value, dict) and value.get('name')
                ]
            except (json.JSONDecodeError, KeyError, TypeError):
                records = []

        if not records:
            legacy_names = self._settings.value('projects/names', [DEFAULT_PROJECT])
            if isinstance(legacy_names, str):
                legacy_names = [legacy_names]
            records = [ProjectRecord(str(name).strip(), 'folder', '') for name in legacy_names]

        return self._normalize_projects(records)

    @staticmethod
    def _normalize_projects(projects: list[ProjectRecord]) -> list[ProjectRecord]:
        unique: list[ProjectRecord] = []
        seen: set[str] = set()
        for project in projects:
            normalized = project.name.casefold()
            if (
                not project.name
                or len(project.name) > MAX_PROJECT_NAME_LENGTH
                or normalized == ALL_PROJECTS.casefold()
                or normalized in seen
            ):
                continue
            unique.append(project)
            seen.add(normalized)
        default_index = next(
            (
                index
                for index, project in enumerate(unique)
                if project.name.casefold() == DEFAULT_PROJECT.casefold()
            ),
            None,
        )
        if default_index is None:
            unique.insert(0, ProjectRecord(DEFAULT_PROJECT, 'folder', ''))
        elif unique[default_index].name != DEFAULT_PROJECT:
            project = unique[default_index]
            unique[default_index] = ProjectRecord(DEFAULT_PROJECT, project.source, project.location)
        return unique

    def _persist_projects(self) -> None:
        self._settings.setValue(
            'projects/records',
            json.dumps([asdict(project) for project in self._projects]),
        )
        self._settings.setValue('projects/names', [project.name for project in self._projects])

    def _find_project(self, name: str) -> ProjectRecord | None:
        normalized = name.strip().casefold()
        return next(
            (project for project in self._projects if project.name.casefold() == normalized),
            None,
        )

    @staticmethod
    def _normalize_github_url(location: str) -> str:
        parsed = urlparse(location.strip())
        parts = [part for part in parsed.path.split('/') if part]
        try:
            port = parsed.port
        except ValueError:
            return ''
        if (
            parsed.scheme != 'https'
            or parsed.hostname is None
            or parsed.hostname.casefold() != 'github.com'
            or parsed.username is not None
            or parsed.password is not None
            or port is not None
            or parsed.query
            or parsed.fragment
            or len(parts) != 2
        ):
            return ''
        owner, repository = parts
        repository = repository.removesuffix('.git')
        if not owner or not repository:
            return ''
        return f'https://github.com/{owner}/{repository}'

    @staticmethod
    def _normalize_folder(location: str) -> str:
        value = location.strip()
        url = QUrl(value)
        if url.isLocalFile():
            value = url.toLocalFile()
        if not value:
            return ''
        path = Path(value).expanduser()
        if not path.is_dir():
            return ''
        try:
            return str(path.resolve())
        except OSError:
            return ''

    def _normalize_location(self, source: str, location: str) -> str:
        if source == 'folder':
            return self._normalize_folder(location)
        if source == 'github':
            return self._normalize_github_url(location)
        return ''

    @staticmethod
    def _suggest_name(source: str, location: str) -> str:
        if source == 'folder':
            value = location.strip()
            url = QUrl(value)
            if url.isLocalFile():
                value = url.toLocalFile()
            return Path(value).name
        if source == 'github':
            parts = [part for part in urlparse(location.strip()).path.split('/') if part]
            return parts[-1].removesuffix('.git') if parts else ''
        return ''

    def _candidate(self, name: str, source: str, location: str) -> ProjectRecord | None:
        source = source.strip().casefold()
        normalized_location = self._normalize_location(source, location)
        candidate_name = name.strip() or self._suggest_name(source, normalized_location)
        if (
            source not in PROJECT_SOURCES
            or not normalized_location
            or not candidate_name
            or len(candidate_name) > MAX_PROJECT_NAME_LENGTH
            or candidate_name.casefold() == ALL_PROJECTS.casefold()
            or self._find_project(candidate_name) is not None
            or any(
                project.source == source
                and project.location.casefold() == normalized_location.casefold()
                for project in self._projects
                if project.location
            )
        ):
            return None
        return ProjectRecord(candidate_name, source, normalized_location)

    @Property('QStringList', notify=projectsChanged)
    def projectNames(self) -> list[str]:  # noqa: N802
        """Return selectable project names, including the aggregate view."""
        return [ALL_PROJECTS, *[project.name for project in self._projects]]

    @Property(str, notify=activeProjectChanged)
    def activeProject(self) -> str:  # noqa: N802
        """Return the project currently displayed in the inbox."""
        return self._active_project

    @Property(str, notify=activeProjectChanged)
    def activeProjectSource(self) -> str:  # noqa: N802
        """Return the selected project's source type."""
        project = self._find_project(self._active_project)
        return project.source if project is not None else ''

    @Property(str, notify=activeProjectChanged)
    def activeProjectLocation(self) -> str:  # noqa: N802
        """Return the selected project's folder or GitHub URL."""
        project = self._find_project(self._active_project)
        return project.location if project is not None else ''

    @Property(str, notify=activeProjectChanged)
    def captureProject(self) -> str:  # noqa: N802
        """Return the concrete project used for a new observation."""
        if self._active_project == ALL_PROJECTS:
            return DEFAULT_PROJECT
        return self._active_project

    @Slot(str)
    def selectProject(self, name: str) -> None:  # noqa: N802
        """Persist and publish a valid active project selection."""
        project = self._find_project(name)
        selected = ALL_PROJECTS if name == ALL_PROJECTS else (project.name if project else '')
        if not selected or selected == self._active_project:
            return
        self._active_project = selected
        self._settings.setValue('projects/active', selected)
        self.activeProjectChanged.emit()

    @Slot(str)
    def registerProject(self, name: str) -> None:  # noqa: N802
        """Migrate a provider project that does not yet expose its location."""
        name = name.strip()
        if (
            not name
            or len(name) > MAX_PROJECT_NAME_LENGTH
            or name.casefold() == ALL_PROJECTS.casefold()
            or self._find_project(name) is not None
        ):
            return
        self._projects.append(ProjectRecord(name, 'folder', ''))
        self._persist_projects()
        self.projectsChanged.emit()

    @Slot(str, str, str, result=bool)
    def canAddProject(self, name: str, source: str, location: str) -> bool:  # noqa: N802
        """Return whether a workspace-backed project can be created."""
        return self._candidate(name, source, location) is not None

    @Slot(str, str, str, result=bool)
    def addProject(self, name: str, source: str, location: str) -> bool:  # noqa: N802
        """Create, persist, and select a workspace-backed project."""
        project = self._candidate(name, source, location)
        if project is None:
            return False
        self._projects.append(project)
        self._persist_projects()
        self.projectsChanged.emit()
        self.selectProject(project.name)
        return True

    @Slot(str, result=str)
    def localPathFromUrl(self, value: str) -> str:  # noqa: N802
        """Convert a folder-dialog URL to a native path for display."""
        url = QUrl(value)
        return url.toLocalFile() if url.isLocalFile() else value
