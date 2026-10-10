"""Tests for the public package version."""

from importlib.metadata import version

from inspyred_dev import __version__


def test_distribution_and_runtime_versions_match() -> None:
    """Keep installed metadata aligned with the runtime package version."""
    assert version('inspyred-dev') == __version__
