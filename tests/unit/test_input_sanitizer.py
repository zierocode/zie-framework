"""Tests for hooks/input-sanitizer.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "input-sanitizer.py")


def run_hook(tool_name, tool_input, cwd_override=None):
    """Run input-sanitizer.py with the given event, optionally overriding CLAUDE_CWD."""
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


# ---------------------------------------------------------------------------
# Write / Edit — relative path resolution
# ---------------------------------------------------------------------------

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
        assert "input-sanitizer" in r.stderr

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


# ---------------------------------------------------------------------------
# Bash — CONFIRM_PATTERNS rewrite
# ---------------------------------------------------------------------------

class TestBashConfirmRewrite:
    def test_rm_rf_dotslash_path_rewritten(self):
        r = run_hook("Bash", {"command": "rm -rf ./dist/"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        cmd = out["updatedInput"]["command"]
        assert "Would run:" in cmd
        assert "read -p" in cmd
        assert "rm -rf ./dist/" in cmd

    def test_rm_f_dotslash_rewritten(self):
        r = run_hook("Bash", {"command": "rm -f ./build/output.o"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_git_clean_fd_rewritten(self):
        r = run_hook("Bash", {"command": "git clean -fd"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_make_clean_rewritten(self):
        r = run_hook("Bash", {"command": "make clean"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_truncate_size_zero_rewritten(self):
        r = run_hook("Bash", {"command": "truncate --size 0 logfile.txt"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_safe_command_produces_no_output(self):
        r = run_hook("Bash", {"command": "echo hello"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_git_status_produces_no_output(self):
        r = run_hook("Bash", {"command": "git status"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_double_wrapping_on_reentrant_call(self):
        """Command already containing confirmation wrapper must not be re-wrapped."""
        already_wrapped = (
            'echo "Would run: rm -rf ./dist/" && read -p "Confirm? [y/N] " _y '
            '&& [ "$_y" = "y" ] && { rm -rf ./dist/; }'
        )
        r = run_hook("Bash", {"command": already_wrapped})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_command_key_exits_cleanly(self):
        r = run_hook("Bash", {"other_key": "value"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_command_exits_cleanly(self):
        r = run_hook("Bash", {"command": ""})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_only_first_pattern_matched_on_multi_match(self):
        """When a command matches multiple CONFIRM_PATTERNS, only one rewrite is applied."""
        r = run_hook("Bash", {"command": "rm -rf ./a/ && make clean"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        # Wrapped exactly once — the wrapping phrase appears exactly once
        assert out["updatedInput"]["command"].count("Would run:") == 1

    def test_whitespace_normalization_matches(self):
        r = run_hook("Bash", {"command": "rm  -rf  ./dist/"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    @pytest.mark.parametrize("command", [
        'rm -rf ./dist "quoted dir"',
        "rm -rf ./it's-mine",
        "rm -rf ./foo; evil",
        "rm -rf ./a && evil",
    ])
    def test_confirm_rewrite_metacharacters_safe(self, command):
        r = run_hook("Bash", {"command": command})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "updatedInput" in out
        assert "permissionDecision" in out
        rewritten_cmd = out["updatedInput"]["command"]
        assert 'printf "Would run: %s\\n"' in rewritten_cmd
        assert f'echo "Would run: {command}"' not in rewritten_cmd
        assert f'{{ {command}; }}' in rewritten_cmd


# ---------------------------------------------------------------------------
# Non-targeted tools
# ---------------------------------------------------------------------------

class TestNonTargetedTools:
    def test_read_tool_produces_no_output(self):
        r = run_hook("Read", {"file_path": "some/file.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_glob_tool_produces_no_output(self):
        r = run_hook("Glob", {"pattern": "**/*.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------

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
        """Event with no tool_name key must exit 0."""
        event = {"tool_input": {"file_path": "src/main.py"}}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_malformed_event_not_dict_exits_zero(self):
        """stdin containing a JSON string (not a dict) must exit 0."""
        r = subprocess.run(
            [sys.executable, HOOK],
            input='"just a string"',
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_deeply_nested_tool_input_missing_file_path_exits_zero(self, tmp_path):
        """Nested tool_input dict without file_path key must exit 0 without crash."""
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


# ---------------------------------------------------------------------------
# hooks.json registration
# ---------------------------------------------------------------------------

class TestHooksJsonRegistration:
    def test_input_sanitizer_registered_in_hooks_json(self):
        hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        pre_tool_hooks = hooks.get("PreToolUse", [])
        all_commands = []
        for entry in pre_tool_hooks:
            for h in entry.get("hooks", []):
                all_commands.append(h.get("command", ""))
        assert any("input-sanitizer.py" in cmd for cmd in all_commands), (
            "input-sanitizer.py must be registered in hooks.json PreToolUse"
        )

    def test_safety_check_still_registered(self):
        hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        pre_tool_hooks = hooks.get("PreToolUse", [])
        all_commands = []
        for entry in pre_tool_hooks:
            for h in entry.get("hooks", []):
                all_commands.append(h.get("command", ""))
        assert any("safety-check.py" in cmd for cmd in all_commands), (
            "safety-check.py must remain registered in hooks.json PreToolUse"
        )


# ---------------------------------------------------------------------------
# Path traversal edge cases
# ---------------------------------------------------------------------------

class TestPathTraversalEdgeCases:
    def test_path_traversal_user_evil_prefix(self, tmp_path):
        """startswith() false-negative: /home/user-evil/ passes the old check.

        With is_relative_to() this must be rejected — hook exits 0, stdout
        empty, stderr contains 'escapes cwd'.
        """
        r = run_hook("Write", {"file_path": "../user-evil/evil.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert "escapes cwd" in r.stderr

    def test_path_nul_byte_rejected(self, tmp_path):
        """NUL byte in file_path must not crash the hook.

        Python's Path() raises ValueError on NUL bytes; the inner except
        block catches it and exits 0.
        """
        r = run_hook("Write", {"file_path": "foo\x00bar.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        if r.stdout.strip():
            json.loads(r.stdout)  # raises if not valid JSON

    def test_path_with_symlink_outside_cwd(self, tmp_path):
        """Symlink inside cwd pointing outside cwd must be rejected.

        .resolve() follows the symlink to its real path; is_relative_to()
        then rejects it because the real path is outside tmp_path.
        """
        link = tmp_path / "link"
        link.symlink_to("/etc")
        r = run_hook("Write", {"file_path": "link/passwd"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""
