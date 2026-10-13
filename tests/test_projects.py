"""Tests for persisted project selection."""

import json

from PySide6.QtCore import QSettings

from inspyred_dev.gui.projects import ALL_PROJECTS, DEFAULT_PROJECT, ProjectContext


def test_project_context_registers_and_persists_selection(tmp_path) -> None:
    """Keep provider-added projects and the active project across launches."""
    settings_path = tmp_path / 'settings.ini'
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)

    projects.registerProject('Website redesign')
    projects.selectProject('Website redesign')
    settings.sync()

    restored = ProjectContext(QSettings(str(settings_path), QSettings.Format.IniFormat))
    assert restored.projectNames == [ALL_PROJECTS, DEFAULT_PROJECT, 'Website redesign']
    assert restored.activeProject == 'Website redesign'
    assert restored.captureProject == 'Website redesign'


def test_all_projects_captures_to_default_project(tmp_path) -> None:
    """Give aggregate-view captures a concrete local project owner."""
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)

    projects.selectProject(ALL_PROJECTS)

    assert projects.activeProject == ALL_PROJECTS
    assert projects.captureProject == DEFAULT_PROJECT


def test_add_folder_project_selects_and_persists_workspace(tmp_path) -> None:
    """Create a project from an existing folder and persist its workspace metadata."""
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)
    workspace = tmp_path / 'website-redesign'
    workspace.mkdir()

    assert projects.addProject('  Website redesign  ', 'folder', str(workspace))
    assert projects.activeProject == 'Website redesign'
    assert projects.activeProjectSource == 'folder'
    assert projects.activeProjectLocation == str(workspace.resolve())
    assert not projects.canAddProject('website REDESIGN', 'folder', str(workspace))
    assert not projects.addProject('Different name', 'folder', str(workspace))
    assert projects.projectNames.count('Website redesign') == 1

    settings.sync()
    restored = ProjectContext(QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat))
    assert restored.activeProjectLocation == str(workspace.resolve())


def test_add_github_project_uses_repository_name_by_default(tmp_path) -> None:
    """Derive a display name and canonical URL from a GitHub repository link."""
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)

    assert projects.addProject('', 'github', 'https://github.com/Inspyre-Softworks/website.git')
    assert projects.activeProject == 'website'
    assert projects.activeProjectSource == 'github'
    assert projects.activeProjectLocation == 'https://github.com/Inspyre-Softworks/website'
    assert projects.githubRepositoryUrls == ['https://github.com/Inspyre-Softworks/website']
    assert not projects.canAddProject('', 'github', 'https://example.com/owner/repo')
    assert not projects.canAddProject('', 'github', 'https://github.com/owner/repo/issues')


def test_add_discovered_github_project_preserves_repository_identity(tmp_path) -> None:
    """Persist stable API identity for a repository chosen from GitHub."""
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)

    assert projects.addGitHubProject(
        '',
        'https://github.com/Inspyre-Softworks/inspyred-dev',
        '12345678901',
        'main',
    )
    records = json.loads(str(settings.value('projects/records')))
    record = next(value for value in records if value['name'] == 'inspyred-dev')

    assert record['github_id'] == 12345678901
    assert record['github_owner'] == 'Inspyre-Softworks'
    assert record['github_name'] == 'inspyred-dev'
    assert record['default_branch'] == 'main'
    assert (
        projects.githubRepositoryUrl('inspyred-dev')
        == 'https://github.com/Inspyre-Softworks/inspyred-dev'
    )
    assert projects.githubRepositoryUrlsExcept('inspyred-dev') == []


def test_edit_project_can_connect_existing_inbox_to_github(tmp_path) -> None:
    """Upgrade an existing project without creating a second inbox."""
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)

    assert projects.editProject(
        DEFAULT_PROJECT,
        DEFAULT_PROJECT,
        'github',
        'https://github.com/Inspyre-Softworks/inspyred-dev',
    )

    assert projects.activeProjectSource == 'github'
    assert (
        projects.githubRepositoryUrl(DEFAULT_PROJECT)
        == 'https://github.com/Inspyre-Softworks/inspyred-dev'
    )
    assert projects.projectNames.count(DEFAULT_PROJECT) == 1


def test_folder_project_is_promoted_when_origin_moves_to_github(tmp_path, monkeypatch) -> None:
    """Periodically recognize a GitHub origin while preserving the local folder."""
    settings_path = tmp_path / 'settings.ini'
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)
    workspace = tmp_path / 'new-repository'
    workspace.mkdir()
    assert projects.addProject('New repository', 'folder', str(workspace))
    monkeypatch.setattr(
        projects,
        '_github_remote_for_folder',
        lambda _: 'https://github.com/example/new-repository',
    )

    projects.checkForGithubProjects()

    assert projects.activeProjectSource == 'github'
    assert projects.activeProjectLocation == 'https://github.com/example/new-repository'
    settings.sync()
    restored = ProjectContext(QSettings(str(settings_path), QSettings.Format.IniFormat))
    record = restored._find_project('New repository')
    assert record is not None
    assert record.local_path == str(workspace.resolve())
