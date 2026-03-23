"""Tests for hooks/safety-check.py"""
import os, sys, json, subprocess, pytest, time
from pathlib import Path

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
