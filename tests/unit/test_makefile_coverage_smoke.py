"""Tests for Makefile coverage-smoke target."""

import subprocess
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.parent)


def test_coverage_smoke_target_exists():
    """make coverage-smoke target must be defined."""
    result = subprocess.run(
        ["make", "--dry-run", "coverage-smoke"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, f"coverage-smoke target missing: {result.stderr}"


def test_make_test_still_includes_unit_and_int():
    """make test must still include test-unit and test-int."""
    result = subprocess.run(
        ["make", "--dry-run", "test"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    combined = result.stdout + result.stderr
    assert "pytest" in combined
    assert "markdownlint" in combined
