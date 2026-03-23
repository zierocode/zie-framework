"""Tests for hooks/safety-check.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(tool_name, command):
    hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    return subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True)


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
