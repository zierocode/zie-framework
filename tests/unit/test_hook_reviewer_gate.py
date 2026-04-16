"""Tests for hooks/reviewer-gate.py — blocks approved:true writes to spec/plan files."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = str(REPO_ROOT / "hooks" / "reviewer-gate.py")


def run_hook(
    tool_name: str, tool_input: dict, cwd: str | None = None, existing_content: str = ""
) -> subprocess.CompletedProcess:
    event = {"tool_name": tool_name, "tool_input": tool_input}
    env = os.environ.copy()
    env["CLAUDE_CWD"] = cwd or str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def write_spec(tmp_path: Path, content: str) -> Path:
    spec_dir = tmp_path / "zie-framework" / "specs"
    spec_dir.mkdir(parents=True)
    f = spec_dir / "2026-04-11-test-feature-design.md"
    f.write_text(content)
    return f


def write_plan(tmp_path: Path, content: str) -> Path:
    plan_dir = tmp_path / "zie-framework" / "plans"
    plan_dir.mkdir(parents=True)
    f = plan_dir / "2026-04-11-test-feature.md"
    f.write_text(content)
    return f


class TestReviewerGateBlocksApproval:
    def test_blocks_write_approved_true_to_spec(self, tmp_path):
        write_spec(tmp_path, "approved: false\n---\n# Spec\n")
        path = "zie-framework/specs/2026-04-11-test-feature-design.md"
        r = run_hook("Write", {"file_path": path, "content": "approved: true\n---\n# Spec\n"}, cwd=str(tmp_path))
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout
        assert "approve.py" in r.stdout

    def test_blocks_edit_approved_true_to_plan(self, tmp_path):
        write_plan(tmp_path, "---\napproved: false\n---\n# Plan\n")
        path = "zie-framework/plans/2026-04-11-test-feature.md"
        r = run_hook("Edit", {"file_path": path, "new_string": "approved: true"}, cwd=str(tmp_path))
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_block_message_names_reviewer_skill(self, tmp_path):
        write_spec(tmp_path, "approved: false\n---\n")
        path = "zie-framework/specs/2026-04-11-test-feature-design.md"
        r = run_hook("Write", {"file_path": path, "content": "approved: true\n"}, cwd=str(tmp_path))
        assert "zie-framework:spec-review" in r.stdout

    def test_block_message_names_plan_reviewer(self, tmp_path):
        write_plan(tmp_path, "---\napproved: false\n---\n")
        path = "zie-framework/plans/2026-04-11-test-feature.md"
        r = run_hook("Write", {"file_path": path, "content": "approved: true\n"}, cwd=str(tmp_path))
        assert "zie-framework:plan-review" in r.stdout


class TestReviewerGateAllows:
    def test_allows_write_without_approved_true(self, tmp_path):
        write_spec(tmp_path, "approved: false\n")
        path = "zie-framework/specs/2026-04-11-test-feature-design.md"
        r = run_hook("Write", {"file_path": path, "content": "approved: false\n---\n# Spec\n"}, cwd=str(tmp_path))
        assert r.returncode == 0

    def test_allows_non_spec_plan_file(self, tmp_path):
        r = run_hook("Write", {"file_path": "hooks/my-hook.py", "content": "approved: true\n"}, cwd=str(tmp_path))
        assert r.returncode == 0

    def test_allows_idempotent_rewrite_of_already_approved_spec(self, tmp_path):
        # File already has approved: true — allow updating other fields
        write_spec(tmp_path, "approved: true\napproved_at: 2026-04-10\n---\n# Spec\n")
        path = "zie-framework/specs/2026-04-11-test-feature-design.md"
        r = run_hook(
            "Write",
            {"file_path": path, "content": "approved: true\napproved_at: 2026-04-11\n---\n# Spec\n"},
            cwd=str(tmp_path),
        )
        assert r.returncode == 0

    def test_allows_bash_tool(self, tmp_path):
        r = run_hook("Bash", {"command": "python3 hooks/approve.py zie-framework/specs/foo.md"}, cwd=str(tmp_path))
        assert r.returncode == 0

    def test_non_spec_plan_path_with_approved_true_allowed(self, tmp_path):
        r = run_hook("Write", {"file_path": "commands/plan.md", "content": "approved: true\n"}, cwd=str(tmp_path))
        assert r.returncode == 0


class TestReviewerGateErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self):
        """Graceful degradation — never block Claude on hook error."""
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not-json",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
