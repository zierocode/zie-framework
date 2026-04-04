"""Tests for Write/Edit path in hooks/safety-check.py (merged from input-sanitizer.py)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "safety-check.py")


def run_hook(tool_name, tool_input, cwd_override=None):
    event = {"tool_name": tool_name, "tool_input": tool_input}
    env = os.environ.copy()
    if cwd_override:
        env["CLAUDE_CWD"] = cwd_override
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


class TestWriteRelativePath:
    def test_relative_path_resolved_to_absolute(self, tmp_path):
        r = run_hook("Write", {"file_path": "src/main.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        assert out["updatedInput"]["file_path"] == str(tmp_path / "src" / "main.py")

    def test_absolute_path_produces_no_output(self, tmp_path):
        abs_path = str(tmp_path / "src" / "main.py")
        r = run_hook("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_traversal_path_produces_no_output(self, tmp_path):
        r = run_hook("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_traversal_path_logs_stderr_warning(self, tmp_path):
        r = run_hook("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
        assert "safety-check" in r.stderr

    def test_missing_file_path_key_exits_cleanly(self):
        r = run_hook("Write", {"content": "hello"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_file_path_exits_cleanly(self):
        r = run_hook("Write", {"file_path": ""})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_other_tool_input_fields_preserved(self, tmp_path):
        r = run_hook(
            "Write",
            {"file_path": "out.txt", "content": "hello world"},
            cwd_override=str(tmp_path),
        )
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["updatedInput"]["content"] == "hello world"

    def test_idempotent_on_already_absolute(self, tmp_path):
        abs_path = str(tmp_path / "already_absolute.py")
        r = run_hook("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestEditRelativePath:
    def test_edit_relative_path_resolved(self, tmp_path):
        r = run_hook("Edit", {"file_path": "hooks/utils.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["updatedInput"]["file_path"] == str(tmp_path / "hooks" / "utils.py")

    def test_edit_absolute_path_unchanged(self, tmp_path):
        abs_path = str(tmp_path / "hooks" / "utils.py")
        r = run_hook("Edit", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestNonTargetedTools:
    def test_read_tool_produces_no_output(self):
        r = run_hook("Read", {"file_path": "some/file.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_glob_tool_produces_no_output(self):
        r = run_hook("Glob", {"pattern": "**/*.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestErrorResilience:
    def test_invalid_json_stdin_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not json at all",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_none_tool_input_exits_zero(self):
        event = {"tool_name": "Write", "tool_input": None}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_tool_name_exits_zero(self):
        event = {"tool_input": {"file_path": "src/main.py"}}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_malformed_event_not_dict_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input='"just a string"',
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_deeply_nested_tool_input_missing_file_path_exits_zero(self, tmp_path):
        event = {
            "tool_name": "Write",
            "tool_input": {
                "nested": {"deeply": {"no_file_path": True}},
                "content": "some content",
            },
        }
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_CWD": str(tmp_path)},
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestPathTraversalEdgeCases:
    def test_path_traversal_user_evil_prefix(self, tmp_path):
        r = run_hook("Write", {"file_path": "../user-evil/evil.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert "escapes cwd" in r.stderr

    def test_path_nul_byte_rejected(self, tmp_path):
        r = run_hook("Write", {"file_path": "foo\x00bar.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        if r.stdout.strip():
            json.loads(r.stdout)  # raises if not valid JSON

    def test_path_with_symlink_outside_cwd(self, tmp_path):
        link = tmp_path / "link"
        link.symlink_to("/etc")
        r = run_hook("Write", {"file_path": "link/passwd"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""
