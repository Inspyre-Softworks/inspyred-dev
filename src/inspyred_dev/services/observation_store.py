"""SQLite persistence for observations.

Author: Taylor B. | Inspyre-Softworks.
"""

from pathlib import Path
import sqlite3

from platformdirs import user_data_dir

from inspyred_dev.core.models import Observation, ObservationStatus, Priority


class ObservationStore:
    """Persist observations locally so capture never depends on network availability."""

    def __init__(self, database_path: Path | None = None) -> None:
        """Open a database and initialize its schema.

        Parameters
        ----------
        database_path : Path | None
            Database location. When omitted, a per-user application data path
            is created.
        """
        if database_path is None:
            data_dir = Path(user_data_dir('Inspyred Dev', 'Inspyre-Softworks'))
            data_dir.mkdir(parents=True, exist_ok=True)
            database_path = data_dir / 'inspyred-dev.sqlite3'

        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    area TEXT NOT NULL DEFAULT '',
                    project TEXT NOT NULL DEFAULT 'Inspyred Dev',
                    screenshot_path TEXT NOT NULL DEFAULT '',
                    github_issue_number INTEGER NOT NULL DEFAULT 0,
                    github_issue_url TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row['name']
                for row in connection.execute('PRAGMA table_info(observations)').fetchall()
            }
            if 'screenshot_path' not in columns:
                connection.execute(
                    "ALTER TABLE observations ADD COLUMN screenshot_path TEXT NOT NULL DEFAULT ''"
                )
            if 'project' not in columns:
                connection.execute(
                    'ALTER TABLE observations ADD COLUMN project TEXT NOT NULL '
                    "DEFAULT 'Inspyred Dev'"
                )
            if 'github_issue_number' not in columns:
                connection.execute(
                    'ALTER TABLE observations ADD COLUMN '
                    'github_issue_number INTEGER NOT NULL DEFAULT 0'
                )
            if 'github_issue_url' not in columns:
                connection.execute(
                    "ALTER TABLE observations ADD COLUMN github_issue_url TEXT NOT NULL DEFAULT ''"
                )

    def add(self, observation: Observation) -> Observation:
        """Insert an observation.

        Parameters
        ----------
        observation : Observation
            Validated observation to persist.

        Returns
        -------
        Observation
            A copy of ``observation`` containing its generated database ID.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO observations (
                    title, details, kind, priority, area, project, screenshot_path, status,
                    created_at, github_issue_number, github_issue_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.title,
                    observation.details,
                    observation.kind.value,
                    observation.priority.value,
                    observation.area,
                    observation.project,
                    observation.screenshot_path,
                    observation.status.value,
                    observation.created_at.isoformat(),
                    observation.github_issue_number,
                    observation.github_issue_url,
                ),
            )
            return observation.model_copy(update={'id': cursor.lastrowid})

    def list_all(
        self,
        project: str | None = None,
        status: ObservationStatus | None = None,
    ) -> list[Observation]:
        """Load all observations.

        Returns
        -------
        list[Observation]
            Persisted observations ordered newest first.
        """
        with self._connect() as connection:
            if project is None and status is None:
                rows = connection.execute(
                    'SELECT * FROM observations ORDER BY created_at DESC, id DESC'
                ).fetchall()
            elif project is not None and status is None:
                rows = connection.execute(
                    'SELECT * FROM observations WHERE project = ? '
                    'ORDER BY created_at DESC, id DESC',
                    (project,),
                ).fetchall()
            elif project is None:
                rows = connection.execute(
                    'SELECT * FROM observations WHERE status = ? ORDER BY created_at DESC, id DESC',
                    (status.value,),
                ).fetchall()
            else:
                rows = connection.execute(
                    'SELECT * FROM observations WHERE project = ? AND status = ? '
                    'ORDER BY created_at DESC, id DESC',
                    (project, status.value),
                ).fetchall()

        return [Observation.model_validate(dict(row)) for row in rows]

    def link_github_issue(self, observation_id: int, issue_number: int, issue_url: str) -> bool:
        """Persist the GitHub issue created from an observation."""
        with self._connect() as connection:
            cursor = connection.execute(
                'UPDATE observations SET github_issue_number = ?, github_issue_url = ? '
                'WHERE id = ?',
                (issue_number, issue_url, observation_id),
            )
            return cursor.rowcount == 1

    def update_status(self, observation_id: int, status: ObservationStatus) -> bool:
        """Persist a workflow-status change for one observation."""
        with self._connect() as connection:
            cursor = connection.execute(
                'UPDATE observations SET status = ? WHERE id = ?',
                (status.value, observation_id),
            )
            return cursor.rowcount == 1

    def update_priority(self, observation_id: int, priority: Priority) -> bool:
        """Persist a priority change for one observation."""
        with self._connect() as connection:
            cursor = connection.execute(
                'UPDATE observations SET priority = ? WHERE id = ?',
                (priority.value, observation_id),
            )
            return cursor.rowcount == 1

    def delete(self, observation_id: int) -> bool:
        """Permanently delete one observation."""
        with self._connect() as connection:
            cursor = connection.execute(
                'DELETE FROM observations WHERE id = ?',
                (observation_id,),
            )
            return cursor.rowcount == 1

    def rename_project(self, old_name: str, new_name: str) -> int:
        """Move observations to a renamed project without changing their identities."""
        with self._connect() as connection:
            cursor = connection.execute(
                'UPDATE observations SET project = ? WHERE project = ?',
                (new_name, old_name),
            )
            return cursor.rowcount
