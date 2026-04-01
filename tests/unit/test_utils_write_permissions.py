"""Tests for /tmp write permission enforcement in utils.py.

Verifies that atomic_write, safe_write_tmp, and safe_write_persistent all
set owner-only (0o600) permissions on the output file.
"""
import os
import sys
from pathlib import Path

HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "hooks"))
sys.path.insert(0, HOOKS_DIR)

from utils import atomic_write, safe_write_persistent, safe_write_tmp


def _mode(path: Path) -> str:
    """Return last-3-digits of octal mode string, e.g. '600'."""
    return oct(path.stat().st_mode)[-3:]


def test_safe_write_tmp_produces_0o600_file(tmp_path):
    """safe_write_tmp must create a file with owner-only 0o600 permissions."""
    target = tmp_path / "test_output.txt"
    result = safe_write_tmp(target, "hello")
    assert result is True, "safe_write_tmp returned False — write failed"
    assert target.exists(), "file was not created"
    assert _mode(target) == "600", (
        f"expected 0o600, got {oct(target.stat().st_mode)}"
    )


def test_safe_write_persistent_produces_0o600_file(tmp_path):
    """safe_write_persistent must create a file with owner-only 0o600 permissions."""
    target = tmp_path / "persistent_output.txt"
    result = safe_write_persistent(target, "world")
    assert result is True, "safe_write_persistent returned False — write failed"
    assert target.exists(), "file was not created"
    assert _mode(target) == "600", (
        f"expected 0o600, got {oct(target.stat().st_mode)}"
    )


def test_atomic_write_produces_0o600_file(tmp_path):
    """atomic_write must create a file with owner-only 0o600 permissions."""
    target = tmp_path / "atomic_output.txt"
    atomic_write(target, "atomic content")
    assert target.exists(), "file was not created"
    assert _mode(target) == "600", (
        f"expected 0o600, got {oct(target.stat().st_mode)}"
    )
