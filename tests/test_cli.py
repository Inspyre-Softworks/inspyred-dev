"""Tests for the Inspyred Dev command-line interface."""

import pytest

from inspyred_dev import __version__
from inspyred_dev.__main__ import main


@pytest.mark.parametrize('flag', ['-v', '--version'])
def test_version_flag(flag: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Print the canonical version for both version flags."""
    with pytest.raises(SystemExit) as exit_info:
        main([flag])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == f'inspyred-dev {__version__}\n'


@pytest.mark.parametrize('flag', ['-h', '--help'])
def test_help_flag(flag: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Print usage and available options for both help flags."""
    with pytest.raises(SystemExit) as exit_info:
        main([flag])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert output.startswith('usage: inspyred-dev')
    assert '-h, --help' in output
    assert '-v, --version' in output
