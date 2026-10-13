"""Tests for Inspyred Dev core models.

Author: Taylor B. | Inspyre-Softworks.
"""

from inspyred_dev.core.models import Observation, ObservationStatus, ObservationType, Priority


def test_observation_defaults() -> None:
    """Apply the expected workflow defaults to a new observation."""
    observation = Observation(title='Add a refresh button')

    assert observation.kind is ObservationType.IDEA
    assert observation.priority is Priority.P2
    assert observation.status is ObservationStatus.INBOX
    assert observation.project == 'Inspyred Dev'
    assert observation.screenshot_path == ''
    assert observation.github_issue_number == 0
    assert observation.github_issue_url == ''
