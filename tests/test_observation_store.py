"""Tests for local observation persistence.

Author: Taylor B. | Inspyre-Softworks.
"""

import sqlite3

from inspyred_dev.core.models import Observation, ObservationStatus, ObservationType, Priority
from inspyred_dev.services.observation_store import ObservationStore


def test_store_round_trip(tmp_path) -> None:
    """Persist and reload an observation without losing its fields."""
    store = ObservationStore(tmp_path / 'test.sqlite3')
    saved = store.add(
        Observation(
            title='Move the button',
            kind=ObservationType.UI,
            project='Website redesign',
            screenshot_path='C:/captures/window.png',
        )
    )

    loaded = store.list_all()

    assert saved.id is not None
    assert len(loaded) == 1
    assert loaded[0].title == 'Move the button'
    assert loaded[0].kind is ObservationType.UI
    assert loaded[0].project == 'Website redesign'
    assert loaded[0].screenshot_path == 'C:/captures/window.png'
    assert loaded[0].github_issue_number == 0
    assert loaded[0].github_issue_url == ''
    assert store.list_all('Website redesign') == loaded
    assert store.list_all('Different project') == []

    assert store.link_github_issue(saved.id, 42, 'https://github.com/example/project/issues/42')
    linked = store.list_all()[0]
    assert linked.github_issue_number == 42
    assert linked.github_issue_url == 'https://github.com/example/project/issues/42'

    assert store.rename_project('Website redesign', 'Website') == 1
    assert store.list_all('Website redesign') == []
    assert store.list_all('Website')[0].id == saved.id

    assert store.update_priority(saved.id, Priority.P1)
    assert store.list_all()[0].priority is Priority.P1
    assert store.update_status(saved.id, ObservationStatus.SHELVED)
    assert store.list_all(status=ObservationStatus.INBOX) == []
    assert store.list_all(status=ObservationStatus.SHELVED)[0].id == saved.id
    assert store.delete(saved.id)
    assert store.list_all() == []


def test_store_migrates_existing_database(tmp_path) -> None:
    """Add the screenshot column to databases created by older releases."""
    database_path = tmp_path / 'legacy.sqlite3'
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL,
                priority TEXT NOT NULL,
                area TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    store = ObservationStore(database_path)
    saved = store.add(Observation(title='Migrated observation'))

    assert saved.id is not None
    assert store.list_all()[0].project == 'Inspyred Dev'
    assert store.list_all()[0].screenshot_path == ''
    assert store.list_all()[0].github_issue_number == 0
    assert store.list_all()[0].github_issue_url == ''
