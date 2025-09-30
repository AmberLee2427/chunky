"""Smoke tests for chunky package metadata."""

from chunky import __version__


def test_version_present() -> None:
    assert __version__
