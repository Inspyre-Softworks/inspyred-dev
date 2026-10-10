"""Tests for quick-capture file management."""

from pathlib import Path

from inspyred_dev.gui.quick_capture import _discard_managed_screenshot


def test_discard_managed_screenshot_removes_capture(tmp_path: Path) -> None:
    """Delete screenshots stored beneath the application's capture directory."""
    capture_dir = tmp_path / 'captures'
    capture_dir.mkdir()
    screenshot = capture_dir / 'window.png'
    screenshot.write_bytes(b'image')

    _discard_managed_screenshot(str(screenshot), capture_dir)

    assert not screenshot.exists()


def test_discard_managed_screenshot_preserves_external_file(tmp_path: Path) -> None:
    """Never delete a user file that is outside the managed capture directory."""
    capture_dir = tmp_path / 'captures'
    capture_dir.mkdir()
    external = tmp_path / 'keep.png'
    external.write_bytes(b'image')

    _discard_managed_screenshot(str(external), capture_dir)

    assert external.exists()
