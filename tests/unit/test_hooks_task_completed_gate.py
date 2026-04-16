"""Tests for hooks/task-completed-gate.py"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "task-completed-gate.py")
IMPL_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb", ".java", ".kt", ".swift", ".c", ".cpp", ".h")


def run_hook(title, cwd=None, env_extra=None):
    event = {"tool_name": "TaskUpdate", "tool_input": {"id": "task-1", "status": "completed", "title": title}}
    env = os.environ.copy()
    if cwd:
        env["CLAUDE_CWD"] = str(cwd)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_lastfailed(cwd: Path, data: dict):
    cache_dir = cwd / ".pytest_cache" / "v" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "lastfailed").write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# Outer guard — bad input
# ---------------------------------------------------------------------------


class TestOuterGuard:
    def test_invalid_json_exits_zero(self):
        r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
        assert r.returncode == 0

    def test_missing_title_exits_zero(self, tmp_path):
        event = {"tool_name": "TaskUpdate", "tool_input": {"id": "t1", "status": "completed"}}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_CWD": str(tmp_path)},
        )
        assert r.returncode == 0

    def test_empty_title_exits_zero(self, tmp_path):
        r = run_hook("", cwd=tmp_path)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Advisory mode — non-implement/fix tasks are passed through
# ---------------------------------------------------------------------------


class TestAdvisoryMode:
    def test_docs_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Write design spec for feature X", cwd=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_plan_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Create implementation plan for auth", cwd=tmp_path)
        assert r.returncode == 0

    def test_review_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Review ADR-009", cwd=tmp_path)
        assert r.returncode == 0

    def test_implement_keyword_triggers_gate(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Implement the session-learn hook", cwd=tmp_path)
        assert r.returncode == 2

    def test_fix_keyword_triggers_gate(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Fix broken wip-checkpoint logic", cwd=tmp_path)
        assert r.returncode == 2

    def test_implement_case_insensitive(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("IMPLEMENT rate limiting", cwd=tmp_path)
        assert r.returncode == 2

    def test_fix_case_insensitive(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("FIX the login bug", cwd=tmp_path)
        assert r.returncode == 2


# ---------------------------------------------------------------------------
# Check 1 — pytest last-failed cache
# ---------------------------------------------------------------------------


class TestPytestCacheCheck:
    def test_failing_tests_block(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True, "tests/test_foo.py::test_baz": True})
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 2
        assert "BLOCKED" in r.stderr
        assert "test_foo" in r.stderr

    def test_empty_lastfailed_passes(self, tmp_path):
        make_lastfailed(tmp_path, {})
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_missing_cache_file_passes(self, tmp_path):
        # No .pytest_cache directory at all
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_missing_cache_dir_passes(self, tmp_path):
        # .pytest_cache exists but lastfailed does not
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_corrupt_lastfailed_passes(self, tmp_path):
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "lastfailed").write_text("NOT VALID JSON {{{")
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_blocked_message_lists_failed_tests(self, tmp_path):
        failures = {f"tests/test_mod.py::test_{i}": True for i in range(7)}
        make_lastfailed(tmp_path, failures)
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 2
        # At most 5 keys shown — count via "::test_" which appears once per key
        total_keys_shown = r.stderr.count("::test_")
        assert total_keys_shown <= 5

    def test_single_failing_test_blocked(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_auth.py::test_login": True})
        r = run_hook("Fix login flow", cwd=tmp_path)
        assert r.returncode == 2
        assert "test_auth" in r.stderr


# ---------------------------------------------------------------------------
# Check 2 — uncommitted implementation files (git status)
# ---------------------------------------------------------------------------


class TestGitStatusCheck:
    def test_no_git_repo_exits_zero(self, tmp_path):
        # tmp_path is not a git repo — git status returns non-zero
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_git_not_found_exits_zero(self, tmp_path):
        # Simulate git not on PATH by patching PATH to empty
        env = os.environ.copy()
        env["PATH"] = "/nonexistent"
        env["CLAUDE_CWD"] = str(tmp_path)
        event = {
            "tool_name": "TaskUpdate",
            "tool_input": {"id": "t1", "status": "completed", "title": "Implement feature X"},
        }
        r = subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, env=env)
        assert r.returncode == 0

    def _make_git_repo_with_uncommitted(self, tmp_path):
        """Create a git repo with an uncommitted .py impl file, no pytest cache."""
        import subprocess as sp

        sp.run(["git", "init"], cwd=tmp_path, capture_output=True)
        sp.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        sp.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "new_hook.py").write_text("# uncommitted impl file")
        return tmp_path

    def test_uncommitted_impl_file_warns(self, tmp_path):
        """Uncommitted impl files produce a warning, not a block."""
        cwd = self._make_git_repo_with_uncommitted(tmp_path)
        r = run_hook("Implement feature X", cwd=cwd)
        assert r.returncode == 0  # uncommitted files never block
        assert "WARNING" in r.stdout

    def test_warning_output_format(self, tmp_path):
        """Warning output contains [zie-framework] prefix."""
        cwd = self._make_git_repo_with_uncommitted(tmp_path)
        r = run_hook("Implement feature X", cwd=cwd)
        assert r.returncode == 0
        assert "[zie-framework]" in r.stdout


# ---------------------------------------------------------------------------
# Extension and test-file filter logic
# ---------------------------------------------------------------------------


class TestFileFilter:
    """Import the hook module and test is_impl_file directly."""

    def _import_filter(self):
        import importlib.machinery
        import types

        loader = importlib.machinery.SourceFileLoader("task_completed_gate", str(HOOK))
        mod = types.ModuleType("task_completed_gate")
        mod.__file__ = str(HOOK)
        loader.exec_module(mod)
        return mod.is_impl_file

    def test_py_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("hooks/session-learn.py") is True

    def test_ts_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.ts") is True

    def test_test_py_file_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("tests/test_session_learn.py") is False

    def test_spec_ts_file_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.spec.ts") is False

    def test_test_dot_ts_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.test.ts") is False

    def test_underscore_test_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/auth_test.go") is False

    def test_md_file_not_impl(self):
        is_impl = self._import_filter()
        assert is_impl("README.md") is False

    def test_go_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("cmd/server/main.go") is True

    def test_rs_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("src/lib.rs") is True


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_advisory_task_completes_quickly(self, tmp_path):
        start = time.time()
        run_hook("Write ADR for caching strategy", cwd=tmp_path)
        assert time.time() - start < 2.0

    def test_gate_task_no_cache_completes_quickly(self, tmp_path):
        start = time.time()
        run_hook("Implement rate limiting middleware", cwd=tmp_path)
        assert time.time() - start < 2.0

    def test_gate_task_with_failing_cache_completes_quickly(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        start = time.time()
        run_hook("Fix broken handler", cwd=tmp_path)
        assert time.time() - start < 2.0


class TestGitTimeout:
    def test_git_timeout_exits_zero(self, tmp_path):
        """task-completed-gate.py must exit 0 when git hangs."""
        import stat

        bin_dir = tmp_path / "fakebin"
        bin_dir.mkdir()
        fake_git = bin_dir / "git"
        fake_git.write_text("#!/bin/sh\nsleep 60\n")
        fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        env["PATH"] = str(bin_dir) + ":" + os.environ.get("PATH", "")
        event = {
            "tool_name": "TaskUpdate",
            "tool_input": {"id": "t1", "status": "completed", "title": "Implement feature X"},
        }
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr
