"""Core data models.

Author: Taylor B. | Inspyre-Softworks.
"""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class ObservationType(StrEnum):
    """Supported observation categories."""

    UI = 'UI'
    UX = 'UX'
    BUG = 'Bug'
    FEATURE = 'Feature'
    REFACTOR = 'Refactor'
    DOCS = 'Docs'
    IDEA = 'Idea'
    TEST = 'Test'
    PERFORMANCE = 'Performance'


class Priority(StrEnum):
    """Observation priority."""

    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'


class ObservationStatus(StrEnum):
    """Workflow state for an observation."""

    INBOX = 'Inbox'
    READY = 'Ready'
    IN_PROGRESS = 'In Progress'
    VERIFY = 'Verify'
    DONE = 'Done'
    SHELVED = 'Shelved'


class Observation(BaseModel):
    """Represent a developer observation captured while using software.

    Attributes
    ----------
    id : int | None
        Database identifier assigned after persistence.
    title : str
        Short observation summary, limited to 500 characters.
    details : str
        Optional supporting context.
    kind : ObservationType
        Category used to classify the observation.
    priority : Priority
        Triage priority.
    area : str
        Optional product or code area.
    project : str
        Local or remote project that owns the observation.
    screenshot_path : str
        Optional local path to the captured active-window screenshot.
    status : ObservationStatus
        Current workflow state.
    created_at : datetime
        Time at which the observation was created.
    """

    id: int | None = None
    title: str = Field(min_length=1, max_length=500)
    details: str = ''
    kind: ObservationType = ObservationType.IDEA
    priority: Priority = Priority.P2
    area: str = ''
    project: str = 'Inspyred Dev'
    screenshot_path: str = ''
    github_issue_number: int = 0
    github_issue_url: str = ''
    status: ObservationStatus = ObservationStatus.INBOX
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
