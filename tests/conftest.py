"""Shared pytest fixtures and configuration for zie-framework tests."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

# Vars injected by Claude Code that must be cleared for test isolation (ADR-015)
_SESSION_VARS_TO_CLEAR = [
    "CLAUDE_SESSION_ID",
    "CLAUDE_TOOL_USE_ID",
    "CLAUDE_AGENT_ID",
    "ZIE_MEMORY_API_KEY",
    "ZIE_MEMORY_API_URL",
]


def run_hook(hook_name: str, event: dict, tmp_cwd=None, extra_env=None) -> subprocess.CompletedProcess:
    """Spawn a hook subprocess with ADR-015 env isolation.

    - Clears all session-injected vars to prevent test contamination.
    - Sets CLAUDE_CWD to tmp_cwd when provided.
    - Merges extra_env last so callers can override individual vars.
    """
    hook_path = REPO_ROOT / "hooks" / hook_name
    env = {k: v for k, v in os.environ.items() if k not in _SESSION_VARS_TO_CLEAR}
    env["ZIE_MEMORY_API_KEY"] = ""
    env["ZIE_MEMORY_API_URL"] = ""
    if tmp_cwd is not None:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if extra_env:
        env.update(extra_env)
    ev = {"session_id": f"test-{abs(hash(str(tmp_cwd))) % 999999}", **event}
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(ev),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def run_hook():
    """pytest fixture that provides the run_hook helper for spawning hooks in tests."""
    def _run(hook_name: str, event: dict, tmp_cwd=None, extra_env=None) -> subprocess.CompletedProcess:
        hook_path = REPO_ROOT / "hooks" / hook_name
        env = {k: v for k, v in os.environ.items() if k not in _SESSION_VARS_TO_CLEAR}
        env["ZIE_MEMORY_API_KEY"] = ""
        env["ZIE_MEMORY_API_URL"] = ""
        if tmp_cwd is not None:
            env["CLAUDE_CWD"] = str(tmp_cwd)
        if extra_env:
            env.update(extra_env)
        ev = {"session_id": f"test-{abs(hash(str(tmp_cwd))) % 999999}", **event}
        return subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(ev),
            capture_output=True,
            text=True,
            env=env,
        )
    return _run


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "error_path: marks tests that exercise hook error paths (missing input, malformed data, subprocess failure)",
    )
