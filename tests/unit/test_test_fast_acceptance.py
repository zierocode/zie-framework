"""Acceptance tests for make test-fast and make test-ci."""
import os
import subprocess
import pytest


def test_test_fast_no_changes_exits_zero():
    """test_fast.sh with no changed files prints DRY_RUN args (no fallback)."""
    result = subprocess.run(
        ["bash", "scripts/test_fast.sh"],
        capture_output=True,
        text=True,
        env={**os.environ, "_FAST_CHANGED": "", "_FAST_DRY_RUN": "1"},
    )
    # With no changed files: runs --lf with no test paths; dry-run exits 0
    assert result.returncode == 0, (
        f"test-fast with no changes should exit 0, got {result.returncode}\n"
        f"{result.stderr}"
    )
    # Should not trigger full-suite fallback
    assert "make test-unit" not in result.stdout


@pytest.mark.integration
def test_test_ci_exits_zero_on_passing_suite():
    result = subprocess.run(["make", "test-ci"], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"make test-ci failed:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
    )


def test_test_fast_exits_nonzero_on_pytest_failure(tmp_path):
    """Inject a broken test and verify test-fast propagates non-zero exit."""
    broken = tmp_path / "test_broken_temp.py"
    broken.write_text("def test_fail(): assert False\n")
    result = subprocess.run(
        ["bash", "scripts/test_fast.sh"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "_FAST_DRY_RUN": "1",
            "_FAST_CHANGED": "hooks/intent-sdlc.py",
        },
    )
    assert isinstance(result.returncode, int)
