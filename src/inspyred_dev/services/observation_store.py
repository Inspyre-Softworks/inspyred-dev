"""SQLite persistence for observations.

Author: Taylor B. | Inspyre-Softworks.
"""

from pathlib import Path
import sqlite3

from platformdirs import user_data_dir

from inspyred_dev.core.models import Observation


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
                '''
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    area TEXT NOT NULL DEFAULT '',
                    project TEXT NOT NULL DEFAULT 'Inspyred Dev',
                    screenshot_path TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                '''
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
                    "ALTER TABLE observations ADD COLUMN project TEXT NOT NULL "
                    "DEFAULT 'Inspyred Dev'"
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
                '''
                INSERT INTO observations (
                    title, details, kind, priority, area, project, screenshot_path, status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
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
                ),
            )
            return observation.model_copy(update={'id': cursor.lastrowid})

    def list_all(self, project: str | None = None) -> list[Observation]:
        """Load all observations.

        Returns
        -------
        list[Observation]
            Persisted observations ordered newest first.
        """
        with self._connect() as connection:
            if project is None:
                rows = connection.execute(
                    'SELECT * FROM observations ORDER BY created_at DESC, id DESC'
                ).fetchall()
            else:
                rows = connection.execute(
                    'SELECT * FROM observations WHERE project = ? '
                    'ORDER BY created_at DESC, id DESC',
                    (project,),
                ).fetchall()

        return [Observation.model_validate(dict(row)) for row in rows]
