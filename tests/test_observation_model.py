"""Tests for observation selection and derived batch actions."""

from PySide6.QtCore import QSettings

from inspyred_dev.core.models import Observation, ObservationStatus, ObservationType, Priority
from inspyred_dev.gui.observation_model import ObservationListModel
from inspyred_dev.gui.projects import ALL_PROJECTS, DEFAULT_PROJECT, ProjectContext
from inspyred_dev.services.observation_store import ObservationStore


def _batch_model(tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    projects = ProjectContext(settings)
    projects.addGitHubProject(
        'Frontend',
        'https://github.com/example/frontend',
        '101',
        'main',
    )
    projects.addGitHubProject(
        'Backend',
        'https://github.com/example/backend',
        '102',
        'main',
    )
    projects.selectProject(ALL_PROJECTS)
    store = ObservationStore(tmp_path / 'observations.sqlite3')
    observations = [
        store.add(
            Observation(
                title='Fix authentication dialog',
                details='The authentication form clips its submit button.',
                kind=ObservationType.BUG,
                priority=Priority.P1,
                area='Authentication',
                project='Frontend',
            )
        ),
        store.add(
            Observation(
                title='Improve settings navigation',
                details='Keep keyboard focus visible in settings.',
                kind=ObservationType.UX,
                priority=Priority.P2,
                area='Settings',
                project='Frontend',
            )
        ),
        store.add(
            Observation(
                title='Speed up API query',
                details='Avoid the duplicate database lookup.',
                kind=ObservationType.PERFORMANCE,
                priority=Priority.P2,
                area='API',
                project='Backend',
            )
        ),
        store.add(
            Observation(
                title='Explain the local setup',
                details='Document how to run the project locally.',
                kind=ObservationType.DOCS,
                priority=Priority.P3,
                area='README',
                project=DEFAULT_PROJECT,
            )
        ),
    ]
    return ObservationListModel(store, projects), observations


def test_selection_is_limited_to_one_project(tmp_path) -> None:
    """Allow multiple notes while keeping every selection project-scoped."""
    model, observations = _batch_model(tmp_path)

    model.toggleSelection(observations[0].id)
    model.toggleSelection(observations[1].id)
    model.toggleSelection(observations[2].id)

    assert model.selectedCount == 2
    assert model.selectedRepositoryCount == 1
    assert model.selectedProjectName == 'Frontend'
    assert model.selectedRepositoryUrl == 'https://github.com/example/frontend'
    assert model.selectedGithubIssueEligible


def test_local_project_notes_can_be_selected_for_ai(tmp_path) -> None:
    """Keep general selection available when a project has no GitHub repository."""
    model, observations = _batch_model(tmp_path)

    model.toggleSelection(observations[3].id)

    assert model.selectedCount == 1
    assert model.selectedProjectName == DEFAULT_PROJECT
    assert not model.selectedGithubIssueEligible
    assert model.buildGithubIssueBatch('one', '') == []
    assert 'Explain the local setup' in model.buildSelectedAiInstructions('combined')


def test_select_all_selects_current_project_notes(tmp_path) -> None:
    """Select every visible note when viewing one project."""
    model, _ = _batch_model(tmp_path)
    model._projects.selectProject('Frontend')

    model.selectAll()

    assert model.count == 2
    assert model.selectedCount == 2
    assert model.selectedProjectName == 'Frontend'


def test_project_rename_moves_existing_notes(tmp_path) -> None:
    """Keep notes attached when project metadata is edited in place."""
    model, observations = _batch_model(tmp_path)

    assert model._projects.editProject(
        'Frontend',
        'Web client',
        'github',
        'https://github.com/example/frontend',
    )

    moved = model._store.list_all('Web client')
    assert {item.id for item in moved} == {observations[0].id, observations[1].id}
    assert model._store.list_all('Frontend') == []


def test_build_issue_batches_for_each_strategy(tmp_path) -> None:
    """Build combined, keyword-grouped, and individual issue payloads."""
    model, observations = _batch_model(tmp_path)
    model.toggleSelection(observations[0].id)
    model.toggleSelection(observations[1].id)

    combined = model.buildGithubIssueBatch('one', '')
    individual = model.buildGithubIssueBatch('individual', '')
    grouped = model.buildGithubIssueBatch('keywords', 'authentication, settings')

    assert len(combined) == 1
    assert set(combined[0]['observation_ids']) == {observations[0].id, observations[1].id}
    assert combined[0]['repository_url'] == 'https://github.com/example/frontend'
    assert 'Fix authentication dialog' in combined[0]['body']
    assert 'Improve settings navigation' in combined[0]['body']
    assert {request['observation_ids'][0] for request in individual} == {
        observations[0].id,
        observations[1].id,
    }
    assert [request['title'] for request in grouped] == [
        'authentication: 1 selected observation(s)',
        'settings: 1 selected observation(s)',
    ]


def test_keyword_batch_puts_unmatched_notes_in_other(tmp_path) -> None:
    """Preserve notes that do not contain any grouping keyword."""
    model, observations = _batch_model(tmp_path)
    model.toggleSelection(observations[0].id)
    model.toggleSelection(observations[1].id)

    grouped = model.buildGithubIssueBatch('keywords', 'authentication')

    assert len(grouped) == 2
    assert grouped[1]['title'] == 'Other: 1 selected observation(s)'
    assert grouped[1]['observation_ids'] == [observations[1].id]


def test_build_ai_instructions_for_single_and_selected_notes(tmp_path) -> None:
    """Produce copy-ready single, combined, and separate coding briefs."""
    model, observations = _batch_model(tmp_path)
    model.toggleSelection(observations[0].id)
    model.toggleSelection(observations[1].id)

    single = model.aiInstructionForObservation(observations[0].id)
    combined = model.buildSelectedAiInstructions('combined')
    separate = model.buildSelectedAiInstructions('individual')

    assert '# Coding instruction: Fix authentication dialog' in single
    assert 'Repository: https://github.com/example/frontend' in single
    assert '# Coding instruction: 2 selected observations' in combined
    assert 'Fix authentication dialog' in combined
    assert 'Improve settings navigation' in combined
    assert separate.count('# Coding instruction:') == 2
    assert '\n\n---\n\n' in separate


def test_shelve_and_restore_moves_note_between_views(tmp_path) -> None:
    """Remove shelved notes from the inbox and allow restoring them later."""
    model, observations = _batch_model(tmp_path)
    observation = observations[0]

    assert model.toggleShelved(observation.id)
    assert observation.id not in {item.id for item in model._items}
    assert model._store.list_all(status=ObservationStatus.SHELVED)[0].id == observation.id

    model.setViewStatus('Shelved')
    assert observation.id in {item.id for item in model._items}
    assert model.toggleShelved(observation.id)
    assert observation.id not in {item.id for item in model._items}
    assert model._store.list_all(status=ObservationStatus.SHELVED) == []


def test_priority_changes_are_bounded_and_persisted(tmp_path) -> None:
    """Move priority toward P1 or P3 without crossing either boundary."""
    model, observations = _batch_model(tmp_path)
    p1_note = observations[0]
    p2_note = observations[1]

    assert not model.increasePriority(p1_note.id)
    assert model.decreasePriority(p1_note.id)
    assert model.increasePriority(p2_note.id)

    saved = {item.id: item for item in model._store.list_all()}
    assert saved[p1_note.id].priority is Priority.P2
    assert saved[p2_note.id].priority is Priority.P1


def test_delete_observation_removes_storage_selection_and_model_row(tmp_path) -> None:
    """Permanently delete a note and clear it from batch selection."""
    model, observations = _batch_model(tmp_path)
    observation = observations[0]
    model.toggleSelection(observation.id)

    assert model.deleteObservation(observation.id)
    assert model.selectedCount == 0
    assert observation.id not in {item.id for item in model._items}
    assert observation.id not in {item.id for item in model._store.list_all()}
