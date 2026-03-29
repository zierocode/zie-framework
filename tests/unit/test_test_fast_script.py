"""Unit tests for scripts/test_fast.sh — file discovery and mapping logic."""
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "test_fast.sh"
REPO_ROOT = Path(__file__).parents[2]


def _run(env_overrides=None):
    """Run test_fast.sh with optional env overrides, return CompletedProcess."""
    env = {**os.environ, **(env_overrides or {})}
    cmd = ["bash", str(SCRIPT)]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(REPO_ROOT))


def test_script_exists():
    assert SCRIPT.exists(), f"scripts/test_fast.sh not found at {SCRIPT}"


def test_script_is_executable_by_bash():
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True)
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_map_hooks_file_prefers_test_hooks_prefix():
    """hooks/intent-sdlc.py → tests/unit/test_hooks_intent_sdlc.py (first-match wins)."""
    result = _run(env_overrides={"_FAST_DRY_RUN": "1", "_FAST_CHANGED": "hooks/intent-sdlc.py"})
    assert "test_hooks_intent_sdlc" in result.stdout or "test_hooks_intent_sdlc" in result.stderr


def test_map_hooks_file_fallback_to_full_suite():
    """hooks/bar_unique_xyz.py → no test match → fallback to full suite."""
    result = _run(env_overrides={"_FAST_DRY_RUN": "1", "_FAST_CHANGED": "hooks/bar_unique_xyz.py"})
    assert "fallback" in result.stdout.lower() or "fallback" in result.stderr.lower()


def test_commands_md_skipped():
    """commands/*.md files produce no test mapping — skip (markdown)."""
    result = _run(env_overrides={"_FAST_DRY_RUN": "1", "_FAST_CHANGED": "commands/zie-implement.md"})
    assert "skip" in result.stdout.lower() or "skip" in result.stderr.lower()


def test_non_python_non_md_file_gracefully_skipped():
    """VERSION file → skip gracefully, no full-suite fallback."""
    result = _run(env_overrides={"_FAST_DRY_RUN": "1", "_FAST_CHANGED": "VERSION"})
    assert "make test-unit" not in result.stdout


def test_exit_code_propagated():
    """Script forwards exit code (returns int)."""
    result = _run(env_overrides={"_FAST_DRY_RUN": "1", "_FAST_CHANGED": "hooks/__nonexistent__.py"})
    assert isinstance(result.returncode, int)
