"""Persisted project selection exposed to QML.

Author: Taylor B. | Inspyre-Softworks.
"""

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

from PySide6.QtCore import Property, QObject, QSettings, QTimer, QUrl, Signal, Slot


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
    github_id: int = 0
    github_owner: str = ''
    github_name: str = ''
    default_branch: str = ''
    local_path: str = ''


class ProjectContext(QObject):
    """Own available workspace projects and the active inbox project."""

    projectsChanged = Signal()
    activeProjectChanged = Signal()
    projectRenamed = Signal(str, str)

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
        self._github_check_timer = QTimer(self)
        self._github_check_timer.setInterval(5 * 60 * 1000)
        self._github_check_timer.timeout.connect(self.checkForGithubProjects)
        self._github_check_timer.start()
        QTimer.singleShot(10_000, self.checkForGithubProjects)

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
                        github_id=int(value.get('github_id', 0) or 0),
                        github_owner=str(value.get('github_owner', '')).strip(),
                        github_name=str(value.get('github_name', '')).strip(),
                        default_branch=str(value.get('default_branch', '')).strip(),
                        local_path=str(
                            value.get(
                                'local_path',
                                value.get('location', '')
                                if value.get('source', 'folder') == 'folder'
                                else '',
                            )
                        ).strip(),
                    )
                    for value in values
                    if isinstance(value, dict) and value.get('name')
                ]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
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
            unique[default_index] = replace(project, name=DEFAULT_PROJECT)
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

    @classmethod
    def _normalize_github_remote(cls, value: str) -> str:
        """Normalize common HTTPS and SSH GitHub remote formats."""
        remote = value.strip()
        normalized = cls._normalize_github_url(remote)
        if normalized:
            return normalized
        if remote.startswith('git@github.com:'):
            path = remote.removeprefix('git@github.com:')
        else:
            parsed = urlparse(remote)
            if parsed.scheme != 'ssh' or parsed.hostname != 'github.com':
                return ''
            path = parsed.path.lstrip('/')
        parts = [part for part in path.split('/') if part]
        if len(parts) != 2:
            return ''
        owner, repository = parts
        repository = repository.removesuffix('.git')
        return f'https://github.com/{owner}/{repository}' if owner and repository else ''

    @classmethod
    def _github_remote_for_folder(cls, folder: str) -> str:
        """Read a folder's origin remote without invoking a command shell."""
        if not folder or not Path(folder).is_dir():
            return ''
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        try:
            result = subprocess.run(
                ['git', '-C', folder, 'remote', 'get-url', 'origin'],
                capture_output=True,
                check=False,
                creationflags=creation_flags,
                text=True,
                timeout=3,
            )
        except (OSError, subprocess.SubprocessError):
            return ''
        return cls._normalize_github_remote(result.stdout) if result.returncode == 0 else ''

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

    def _candidate(
        self,
        name: str,
        source: str,
        location: str,
        github_id: int = 0,
        default_branch: str = '',
    ) -> ProjectRecord | None:
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
        owner = ''
        repository = ''
        if source == 'github':
            owner, repository = [
                part for part in urlparse(normalized_location).path.split('/') if part
            ]
        return ProjectRecord(
            candidate_name,
            source,
            normalized_location,
            max(0, github_id),
            owner,
            repository,
            default_branch.strip(),
            normalized_location if source == 'folder' else '',
        )

    @Property('QStringList', notify=projectsChanged)
    def projectNames(self) -> list[str]:  # noqa: N802
        """Return selectable project names, including the aggregate view."""
        return [ALL_PROJECTS, *[project.name for project in self._projects]]

    @Property('QStringList', notify=projectsChanged)
    def githubRepositoryUrls(self) -> list[str]:  # noqa: N802
        """Return canonical GitHub URLs already represented by projects."""
        return [
            project.location
            for project in self._projects
            if project.source == 'github' and project.location
        ]

    @Slot(str, result='QStringList')
    def githubRepositoryUrlsExcept(self, project_name: str) -> list[str]:  # noqa: N802
        """Return repository exclusions while allowing one project to edit itself."""
        excluded = project_name.strip().casefold()
        return [
            project.location
            for project in self._projects
            if project.source == 'github'
            and project.location
            and project.name.casefold() != excluded
        ]

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

    @Slot(str, str, str, str, result=bool)
    def addGitHubProject(  # noqa: N802
        self,
        name: str,
        location: str,
        github_id: str,
        default_branch: str,
    ) -> bool:
        """Create a GitHub project while preserving its API identity."""
        try:
            repository_id = int(github_id)
        except ValueError:
            repository_id = 0
        project = self._candidate(name, 'github', location, repository_id, default_branch)
        if project is None:
            return False
        self._projects.append(project)
        self._persist_projects()
        self.projectsChanged.emit()
        self.selectProject(project.name)
        return True

    def _edit_candidate(
        self,
        original_name: str,
        name: str,
        source: str,
        location: str,
        github_id: int = 0,
        default_branch: str = '',
    ) -> ProjectRecord | None:
        current = self._find_project(original_name)
        source = source.strip().casefold()
        normalized_location = self._normalize_location(source, location)
        candidate_name = name.strip() or self._suggest_name(source, normalized_location)
        if current is None or current.name == DEFAULT_PROJECT:
            candidate_name = current.name if current is not None else candidate_name
        if (
            current is None
            or source not in PROJECT_SOURCES
            or not normalized_location
            or not candidate_name
            or len(candidate_name) > MAX_PROJECT_NAME_LENGTH
            or candidate_name.casefold() == ALL_PROJECTS.casefold()
            or any(
                project.name.casefold() == candidate_name.casefold()
                and project.name.casefold() != current.name.casefold()
                for project in self._projects
            )
            or any(
                project.source == source
                and project.location.casefold() == normalized_location.casefold()
                and project.name.casefold() != current.name.casefold()
                for project in self._projects
                if project.location
            )
        ):
            return None
        owner = ''
        repository = ''
        if source == 'github':
            owner, repository = [
                part for part in urlparse(normalized_location).path.split('/') if part
            ]
            if (
                current.source == 'github'
                and current.location.casefold() == normalized_location.casefold()
            ):
                github_id = github_id or current.github_id
                default_branch = default_branch or current.default_branch
        local_path = (
            normalized_location
            if source == 'folder'
            else current.local_path
            or (current.location if current.source == 'folder' else '')
        )
        return ProjectRecord(
            candidate_name,
            source,
            normalized_location,
            max(0, github_id),
            owner,
            repository,
            default_branch.strip(),
            local_path,
        )

    @Slot(str, str, str, str, result=bool)
    def canEditProject(  # noqa: N802
        self,
        original_name: str,
        name: str,
        source: str,
        location: str,
    ) -> bool:
        """Return whether the edited project metadata is valid and unique."""
        return self._edit_candidate(original_name, name, source, location) is not None

    def _apply_project_edit(self, original_name: str, project: ProjectRecord | None) -> bool:
        current = self._find_project(original_name)
        if current is None or project is None:
            return False
        index = self._projects.index(current)
        self._projects[index] = project
        was_active = self._active_project == current.name
        if was_active:
            self._active_project = project.name
            self._settings.setValue('projects/active', project.name)
        self._persist_projects()
        if current.name != project.name:
            self.projectRenamed.emit(current.name, project.name)
        self.projectsChanged.emit()
        if was_active:
            self.activeProjectChanged.emit()
        return True

    @Slot(str, str, str, str, result=bool)
    def editProject(  # noqa: N802
        self,
        original_name: str,
        name: str,
        source: str,
        location: str,
    ) -> bool:
        """Edit a project, including manually connecting it to GitHub."""
        return self._apply_project_edit(
            original_name,
            self._edit_candidate(original_name, name, source, location),
        )

    @Slot(str, str, str, str, str, result=bool)
    def editGitHubProject(  # noqa: N802
        self,
        original_name: str,
        name: str,
        location: str,
        github_id: str,
        default_branch: str,
    ) -> bool:
        """Edit a project using repository metadata returned by GitHub."""
        try:
            repository_id = int(github_id)
        except ValueError:
            repository_id = 0
        return self._apply_project_edit(
            original_name,
            self._edit_candidate(
                original_name,
                name,
                'github',
                location,
                repository_id,
                default_branch,
            ),
        )

    @Slot()
    def checkForGithubProjects(self) -> None:  # noqa: N802
        """Promote local folder projects whose origin remote now points to GitHub."""
        changed = False
        used_urls = {
            project.location.rstrip('/').casefold()
            for project in self._projects
            if project.source == 'github'
        }
        for index, project in enumerate(self._projects):
            if project.source != 'folder':
                continue
            folder = project.local_path or project.location
            if not folder:
                continue
            repository_url = self._github_remote_for_folder(folder)
            if not repository_url or repository_url.rstrip('/').casefold() in used_urls:
                continue
            owner, repository = [
                part for part in urlparse(repository_url).path.split('/') if part
            ]
            self._projects[index] = ProjectRecord(
                project.name,
                'github',
                repository_url,
                github_owner=owner,
                github_name=repository,
                local_path=folder,
            )
            used_urls.add(repository_url.rstrip('/').casefold())
            changed = True
        if not changed:
            return
        self._persist_projects()
        self.projectsChanged.emit()
        self.activeProjectChanged.emit()

    @Slot(str, result=str)
    def githubRepositoryUrl(self, project_name: str) -> str:  # noqa: N802
        """Return the GitHub repository URL attached to a named project."""
        project = self._find_project(project_name)
        if project is None or project.source != 'github':
            return ''
        return project.location

    @Slot(str, result=str)
    def localPathFromUrl(self, value: str) -> str:  # noqa: N802
        """Convert a folder-dialog URL to a native path for display."""
        url = QUrl(value)
        return url.toLocalFile() if url.isLocalFile() else value
