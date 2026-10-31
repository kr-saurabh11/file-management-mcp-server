"""Pytest configuration and shared fixtures for FastMCP File Management Server tests."""

from pathlib import Path
import pytest


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Provide an isolated temporary directory for file-based tests.

    Args:
        tmp_path: Built-in pytest fixture providing a unique temporary directory
            path object for each test invocation.

    Returns:
        Path: An isolated, clean Path instance for creating, reading, editing,
            and deleting test files.
    """
    return tmp_path
