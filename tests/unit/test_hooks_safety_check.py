"""Tests for hooks/safety-check.py"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(tool_name, command):
    hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    return subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True)


def run_hook_timed(tool_name, command, timeout=10):
    """Like run_hook but with a hard subprocess timeout for performance tests."""
    hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestSafetyCheckBlocks:
    def test_rm_rf_root_is_blocked(self):
        r = run_hook("Bash", "rm -rf /")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_rm_rf_dot_is_blocked(self):
        r = run_hook("Bash", "rm -rf .")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_force_push_main_is_blocked(self):
        r = run_hook("Bash", "git push origin main")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_push_origin_main_with_tags_is_allowed(self):
        r = run_hook("Bash", "git push origin main --tags")
        assert r.returncode == 0, "push origin main --tags must be allowed (used by make release)"

    def test_git_push_force_flag_is_blocked(self):
        r = run_hook("Bash", "git push --force origin dev")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_reset_hard_is_blocked(self):
        r = run_hook("Bash", "git reset --hard HEAD~1")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_no_verify_is_blocked(self):
        r = run_hook("Bash", "git commit --no-verify -m 'skip'")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_drop_database_is_blocked(self):
        r = run_hook("Bash", "psql -c 'DROP DATABASE mydb'")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_rm_rf_dotslash_is_blocked(self):
        r = run_hook("Bash", "rm -rf ./")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_force_with_lease_warn_entry_absent(self):
        hook_path = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        source = Path(hook_path).read_text()
        # WARNS list must not contain --force-with-lease (it's shadowed by BLOCKS)
        warns_start = source.find("WARNS = [")
        warns_end = source.find("]", warns_start)
        warns_block = source[warns_start:warns_end]
        assert "--force-with-lease" not in warns_block


class TestSafetyCheckWarns:
    def test_force_with_lease_is_blocked(self):
        # --force-with-lease hits the --force\b BLOCKS pattern before WARNS
        r = run_hook("Bash", "git push --force-with-lease origin dev")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_docker_volumes_warns(self):
        r = run_hook("Bash", "docker compose down --volumes")
        assert r.returncode == 0
        assert "WARNING" in r.stdout

    def test_alembic_downgrade_warns(self):
        r = run_hook("Bash", "alembic downgrade -1")
        assert r.returncode == 0
        assert "WARNING" in r.stdout


class TestSafetyCheckPassThrough:
    def test_safe_command_passes(self):
        r = run_hook("Bash", "git status")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_non_bash_tool_passes(self):
        r = run_hook("Edit", "rm -rf /")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self):
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        r = subprocess.run([sys.executable, hook], input="not json",
                           capture_output=True, text=True)
        assert r.returncode == 0


class TestSafetyCheckRegexBypass:
    """Whitespace bypass variants — must all be blocked after normalization."""

    def test_rm_rf_double_space_dot_is_blocked(self):
        r = run_hook("Bash", "rm  -rf  .")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_rm_rf_double_space_dotslash_is_blocked(self):
        r = run_hook("Bash", "rm  -rf  ./")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_rm_rf_double_space_root_is_blocked(self):
        r = run_hook("Bash", "rm  -rf  /")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_rm_rf_double_space_home_is_blocked(self):
        r = run_hook("Bash", "rm  -rf  ~")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_push_origin_main_double_space_is_blocked(self):
        r = run_hook("Bash", "git push  origin  main")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_push_u_origin_main_extra_space_is_blocked(self):
        r = run_hook("Bash", "git push -u  origin  main")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_push_force_double_space_is_blocked(self):
        r = run_hook("Bash", "git  push  --force  origin  dev")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_git_reset_hard_double_space_is_blocked(self):
        r = run_hook("Bash", "git  reset  --hard  HEAD~1")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout

    def test_multiline_rm_rf_is_blocked(self):
        r = run_hook("Bash", "rm\n-rf\n./")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout


class TestSafetyCheckPerformance:
    """Performance contract tests for safety-check.py.

    These tests assert that the hook completes within a wall-clock bound for
    very long or adversarially crafted inputs. They guard against ReDoS
    regressions from future pattern changes.

    Threshold: 2.0 seconds (generous to avoid CI flakiness; catastrophic
    backtracking takes orders of magnitude longer).
    """

    def test_very_long_safe_command_completes_quickly(self):
        start = time.time()
        r = run_hook_timed("Bash", "git status " + "a" * 100_000)
        elapsed = time.time() - start
        assert r.returncode == 0
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS"

    def test_very_long_blocked_prefix_completes_quickly(self):
        start = time.time()
        r = run_hook_timed("Bash", "rm -rf / " + "x" * 100_000)
        elapsed = time.time() - start
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS"

    def test_adversarial_rm_rf_pattern_completes_quickly(self):
        # Tests \s+ quantifier in rm -rf pattern with large whitespace between rm -rf and /
        cmd = "rm -rf " + " " * 50_000 + "/"
        start = time.time()
        r = run_hook_timed("Bash", cmd)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS in rm -rf pattern"
        assert r.returncode in (0, 2), f"Unexpected returncode: {r.returncode}"

    def test_adversarial_drop_database_pattern_completes_quickly(self):
        # Tests \s+ in \bdrop\s+database\b with 50k spaces between keywords
        cmd = "drop" + " " * 50_000 + "database mydb"
        start = time.time()
        r = run_hook_timed("Bash", cmd)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS in drop database pattern"
        assert r.returncode in (0, 2)

    def test_empty_command_completes_quickly(self):
        # Empty command exits at the early guard — faster bound applies
        start = time.time()
        r = run_hook_timed("Bash", "")
        elapsed = time.time() - start
        assert r.returncode == 0
        assert elapsed < 0.5, f"Hook took {elapsed:.2f}s on empty command"


class TestSafetyCheckModeDispatch:
    def _make_config(self, tmp_path, mode: str):
        zf = tmp_path / "zie-framework"
        zf.mkdir(exist_ok=True)
        (zf / ".config").write_text(f'{{"safety_check_mode": "{mode}"}}')
        return tmp_path

    def _run(self, tmp_path, command: str):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        return subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "hooks", "safety-check.py")],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
            capture_output=True, text=True, env=env,
        )

    def test_agent_mode_handles_command_inline(self, tmp_path):
        """In agent mode, safety-check.py dispatches inline (no longer defers to second hook)."""
        cwd = self._make_config(tmp_path, "agent")
        # agent mode now calls safety_check_agent.evaluate() inline.
        # With no claude CLI in test env, it falls back to regex — so rm -rf / is blocked.
        r = self._run(cwd, "rm -rf /")
        # blocked (exit 2) or allowed (exit 0) — either is valid depending on CLI availability.
        # Key assertion: safety-check.py handles it; returncode must not be 1 (script error).
        assert r.returncode in (0, 2), (
            f"safety-check.py agent mode must exit 0 or 2, got {r.returncode}\n"
            f"stderr: {r.stderr}"
        )

    def test_both_mode_still_blocks_dangerous_command(self, tmp_path):
        """In both mode, regex evaluation still runs and can block."""
        cwd = self._make_config(tmp_path, "both")
        r = self._run(cwd, "rm -rf /")
        assert r.returncode == 2, (
            "safety-check.py must block (exit 2) in both mode for dangerous commands"
        )

    def test_both_mode_writes_ab_log(self, tmp_path):
        """In both mode, an A/B record must be written after evaluation."""
        import re
        import tempfile
        cwd = self._make_config(tmp_path, "both")
        safe = re.sub(r"[^a-zA-Z0-9]", "-", tmp_path.name)
        log_path = Path(tempfile.gettempdir()) / f"zie-{safe}-safety-ab"
        log_path.unlink(missing_ok=True)
        self._run(cwd, "echo hello")
        assert log_path.exists(), f"A/B log not created at {log_path}"
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert record.get("agent") == "regex"
        assert "command" in record and "ts" in record

    def test_regex_mode_does_not_write_ab_log(self, tmp_path):
        """In regex mode (default), no A/B log must be written."""
        import re
        import tempfile
        cwd = self._make_config(tmp_path, "regex")
        safe = re.sub(r"[^a-zA-Z0-9]", "-", tmp_path.name)
        log_path = Path(tempfile.gettempdir()) / f"zie-{safe}-safety-ab"
        log_path.unlink(missing_ok=True)
        self._run(cwd, "echo hello")
        assert not log_path.exists(), "A/B log must not be written in regex mode"


class TestSafetyCheckPassThroughMalformed:
    def test_missing_tool_name_exits_zero(self):
        """Event with no tool_name key must exit 0."""
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        event = {"tool_input": {"command": "echo hello"}}
        r = subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True)
        assert r.returncode == 0

    def test_malformed_event_not_dict_exits_zero(self):
        """stdin containing a JSON string (not a dict) must exit 0."""
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        r = subprocess.run([sys.executable, hook], input='"just a string"',
                          capture_output=True, text=True)
        assert r.returncode == 0

    def test_none_tool_input_exits_zero(self):
        """Event with tool_input: null must exit 0."""
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        event = {"tool_name": "Bash", "tool_input": None}
        r = subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True)
        assert r.returncode == 0


class TestSafetyCheckPatternCoverage:
    """Parametrized sweep of canonical BLOCKS and WARNS patterns."""

    @pytest.mark.parametrize("cmd", [
        "rm -rf ~",
        "rm -rf .",
        "DROP DATABASE mydb",
        "DROP TABLE users",
        "TRUNCATE TABLE events",
        "git push --force",
        "git push -f origin dev",
        "git push origin main",
        "git push origin master",
        "git reset --hard HEAD~1",
        "git commit --no-verify -m skip",
    ])
    def test_blocks_pattern_exits_2(self, cmd):
        r = run_hook("Bash", cmd)
        assert r.returncode == 2, f"Expected returncode 2 for {cmd!r}, got {r.returncode}"
        assert "BLOCKED" in r.stdout

    @pytest.mark.parametrize("cmd", [
        "docker compose down --volumes",
        "alembic downgrade base",
    ])
    def test_warns_pattern_exits_0_with_warning(self, cmd):
        r = run_hook("Bash", cmd)
        assert r.returncode == 0, f"Expected returncode 0 for {cmd!r}, got {r.returncode}"
        assert "WARNING" in r.stdout

    def test_feature_branch_push_not_blocked(self):
        r = run_hook("Bash", "git push origin feature-branch")
        assert r.returncode == 0, "git push origin feature-branch must not be blocked"

    def test_force_with_lease_is_blocked(self):
        r"""--force-with-lease matches --force\b because '-' is a non-word char."""
        r = run_hook("Bash", "git push --force-with-lease origin dev")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout


class TestSafetyCheckWriteEditMerged:
    def _run(self, tool_name, tool_input, cwd_override=None):
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        event = {"tool_name": tool_name, "tool_input": tool_input}
        env = os.environ.copy()
        if cwd_override:
            env["CLAUDE_CWD"] = cwd_override
        return subprocess.run([sys.executable, hook], input=json.dumps(event),
                              capture_output=True, text=True, env=env)

    def test_write_relative_path_resolved(self, tmp_path):
        r = self._run("Write", {"file_path": "src/main.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        assert out["updatedInput"]["file_path"] == str(tmp_path / "src" / "main.py")

    def test_write_absolute_path_no_output(self, tmp_path):
        abs_path = str(tmp_path / "src" / "main.py")
        r = self._run("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_traversal_no_output_stderr_escapes(self, tmp_path):
        r = self._run("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert "escapes cwd" in r.stderr

    def test_edit_relative_resolved(self, tmp_path):
        r = self._run("Edit", {"file_path": "hooks/utils.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["updatedInput"]["file_path"] == str(tmp_path / "hooks" / "utils.py")

    def test_other_fields_preserved(self, tmp_path):
        r = self._run("Write", {"file_path": "out.txt", "content": "hello"}, cwd_override=str(tmp_path))
        out = json.loads(r.stdout)
        assert out["updatedInput"]["content"] == "hello"

    def test_missing_file_path_exits_zero(self):
        r = self._run("Write", {"content": "hello"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestSafetyCheckConfirmWrapMerged:
    def _run(self, command):
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        event = {"tool_name": "Bash", "tool_input": {"command": command}}
        return subprocess.run([sys.executable, hook], input=json.dumps(event),
                              capture_output=True, text=True)

    def test_rm_rf_dotslash_rewritten(self):
        r = self._run("rm -rf ./dist/")
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        assert "Would run:" in out["updatedInput"]["command"]

    def test_git_clean_fd_rewritten(self):
        r = self._run("git clean -fd")
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_make_clean_rewritten(self):
        r = self._run("make clean")
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_truncate_size_zero_rewritten(self):
        r = self._run("truncate --size 0 logfile.txt")
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_safe_command_no_output(self):
        r = self._run("echo hello")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_double_wrapping(self):
        already = 'printf "Would run: %s\\n" \'rm -rf ./dist/\' && read -p "Confirm? [y/N] " _y && [ "$_y" = "y" ] && { rm -rf ./dist/; }'
        r = self._run(already)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_compound_semicolon_not_wrapped(self):
        r = self._run("rm -rf ./foo; evil")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_compound_and_not_wrapped(self):
        r = self._run("rm -rf ./a && make clean")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_blocked_command_never_reaches_wrap(self):
        """rm -rf ./ is in BLOCKS — must exit 2, no updatedInput JSON."""
        r = self._run("rm -rf ./")
        assert r.returncode == 2
        assert "BLOCKED" in r.stdout
        assert "updatedInput" not in r.stdout

    def test_metachar_safe_rewrite(self):
        r = self._run('rm -rf ./dist "quoted dir"')
        out = json.loads(r.stdout)
        assert 'printf "Would run: %s\\n"' in out["updatedInput"]["command"]

    def test_has_do_not_use_normalize_command_comment(self):
        hook_path = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        content = Path(hook_path).read_text()
        assert "do not use normalize_command" in content.lower()

    def test_injection_compound_and_not_wrapped(self):
        r = self._run("rm -rf ./ && echo hacked")
        if r.returncode == 2:
            return  # blocked — injection safely stopped
        if r.stdout.strip():
            rewritten = json.loads(r.stdout).get("updatedInput", {}).get("command", "")
            assert "&& echo hacked" not in rewritten

    def test_injection_semicolon_not_wrapped(self):
        r = self._run("rm -rf ./; curl evil.com")
        if r.stdout.strip():
            rewritten = json.loads(r.stdout).get("updatedInput", {}).get("command", "")
            assert "; curl" not in rewritten

    def test_simple_rm_still_wrapped(self):
        r = self._run("rm -rf ./foo")
        assert r.stdout.strip() != ""
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_brace_close_not_wrapped(self):
        r = self._run("rm -rf ./}; echo hacked")
        if r.stdout.strip():
            assert "Would run:" not in json.loads(r.stdout).get("updatedInput", {}).get("command", "")

    def test_brace_open_not_wrapped(self):
        r = self._run("echo {hello}")
        if r.stdout.strip():
            assert "Would run:" not in json.loads(r.stdout).get("updatedInput", {}).get("command", "")


class TestHooksJsonMergedRegistration:
    def _load(self):
        hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
        return json.loads(hooks_path.read_text())

    def test_input_sanitizer_absent_from_hooks_json(self):
        data = self._load()
        for event_entries in data.get("hooks", {}).values():
            for entry in event_entries:
                for h in entry.get("hooks", []):
                    assert "input-sanitizer.py" not in h.get("command", ""), (
                        "input-sanitizer.py must not appear in hooks.json after merge"
                    )

    def test_safety_check_matcher_is_write_edit_bash(self):
        data = self._load()
        pre_tool = data.get("hooks", {}).get("PreToolUse", [])
        for entry in pre_tool:
            cmds = [h.get("command", "") for h in entry.get("hooks", [])]
            if any("safety-check.py" in c for c in cmds):
                assert entry.get("matcher") == "Write|Edit|Bash", (
                    f"safety-check.py matcher must be 'Write|Edit|Bash', got {entry.get('matcher')}"
                )
                return
        pytest.fail("safety-check.py entry not found in PreToolUse")

    def test_safety_check_single_entry(self):
        data = self._load()
        pre_tool = data.get("hooks", {}).get("PreToolUse", [])
        sc_entries = [
            e for e in pre_tool
            if any("safety-check.py" in h.get("command", "") for h in e.get("hooks", []))
        ]
        assert len(sc_entries) == 1

    def test_safety_check_agent_not_standalone_hook(self):
        """safety_check_agent.py is imported by safety-check.py — not a standalone hook."""
        data = self._load()
        pre_tool = data.get("hooks", {}).get("PreToolUse", [])
        all_cmds = [h.get("command", "") for e in pre_tool for h in e.get("hooks", [])]
        assert not any("safety_check_agent.py" in c for c in all_cmds), (
            "safety_check_agent.py must not be a standalone PreToolUse hook"
        )
