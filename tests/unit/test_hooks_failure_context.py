"""Tests for hooks/failure-context.py — PostToolUseFailure debug context."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "failure-context.py")
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))

SAMPLE_ROADMAP = """## Now\n- [ ] Implement failure-context hook\n"""
ROADMAP_EMPTY_NOW = """## Now\n\n## Next\n- [ ] Some future task\n"""


def run_hook(event: dict, tmp_cwd=None, env_overrides=None):
    env = {**os.environ}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


# ── Test cases ────────────────────────────────────────────────────────────


class TestNormalFailure:
    """TC-1: Normal failure with ROADMAP Now item present."""

    def test_additionalcontext_contains_task(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Bash"}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "additionalContext" in data
        assert "Implement failure-context hook" in data["additionalContext"]

    def test_additionalcontext_contains_branch(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Bash"}
        result = run_hook(event, tmp_cwd=cwd)
        data = json.loads(result.stdout)
        assert "Branch:" in data["additionalContext"]

    def test_additionalcontext_contains_last_commit(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Bash"}
        result = run_hook(event, tmp_cwd=cwd)
        data = json.loads(result.stdout)
        assert "Last commit:" in data["additionalContext"]

    def test_additionalcontext_contains_quick_fix_hint(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Edit"}
        result = run_hook(event, tmp_cwd=cwd)
        data = json.loads(result.stdout)
        assert "make test-unit" in data["additionalContext"]


class TestInterrupt:
    """TC-2: is_interrupt: true — hook must emit nothing."""

    def test_empty_stdout_on_interrupt(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Bash", "is_interrupt": True}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exit_zero_on_interrupt(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {"tool_name": "Write", "is_interrupt": True}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0


class TestMissingRoadmap:
    """TC-3: ROADMAP.md absent — active task fallback."""

    def test_fallback_task_when_roadmap_missing(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=None)
        event = {"tool_name": "Write"}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "(none — check ROADMAP Now lane)" in data["additionalContext"]


class TestEmptyNowLane:
    """TC-4: ROADMAP Now lane has no items."""

    def test_fallback_task_when_now_lane_empty(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_EMPTY_NOW)
        event = {"tool_name": "Bash"}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "(none — check ROADMAP Now lane)" in data["additionalContext"]


class TestToolFilter:
    """TC-5: Tool not in {Bash, Write, Edit} — emit nothing."""

    @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "ListFiles", ""])
    def test_empty_stdout_for_out_of_scope_tool(self, tmp_path, tool):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": tool}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        assert result.stdout == ""

    def test_missing_tool_name_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {}  # no tool_name key at all
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        assert result.stdout == ""


class TestGitUnavailable:
    """TC-6: git unavailable — both git fields use fallback string."""

    def test_git_unavailable_fallback(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Bash"}
        # Override PATH to an empty dir so git cannot be found
        env_overrides = {"PATH": str(tmp_path)}
        result = run_hook(event, tmp_cwd=cwd, env_overrides=env_overrides)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        ctx = data["additionalContext"]
        assert "(git unavailable)" in ctx


class TestOutputProtocol:
    """TC-7: Output is valid JSON with additionalContext key."""

    @pytest.mark.parametrize("tool", ["Bash", "Write", "Edit"])
    def test_valid_json_output(self, tmp_path, tool):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": tool}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)
        assert "additionalContext" in parsed
        assert isinstance(parsed["additionalContext"], str)

    def test_output_is_single_json_object(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        event = {"tool_name": "Edit"}
        result = run_hook(event, tmp_cwd=cwd)
        assert result.stdout.strip() != ""
        json.loads(result.stdout)  # raises if invalid
