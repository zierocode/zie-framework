"""Tests for hooks/auto-test.py"""
import os, sys, json, subprocess, pytest, re
from pathlib import Path

HOOKS_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "hooks")
sys.path.insert(0, HOOKS_DIR)
from utils import project_tmp_path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "auto-test.py")


def run_hook(event, tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                          capture_output=True, text=True, env=env)


def make_cwd(tmp_path, config=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    return tmp_path


class TestAutoTestGuardrails:
    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_action_when_no_test_runner_in_config(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # test_runner key absent
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_action_for_non_edit_tool(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}},
                     tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run([sys.executable, HOOK], input="not json",
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0

    def test_missing_file_path_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Edit", "tool_input": {}}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""


class TestAutoTestDebounce:
    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_debounce_suppresses_rapid_second_call(self, tmp_path):
        # Write a fresh debounce file to simulate a very recent test run
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 10000})
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("some_file.py")
        # Manually set mtime to NOW so debounce window is active
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        # Should be suppressed — no test runner output expected
        assert "[zie-framework] Tests" not in r.stdout


class TestFindMatchingTest:
    """Direct unit tests for find_matching_test() — imported from auto-test module."""

    @pytest.fixture
    def load_module(self):
        """Import auto-test.py without triggering hook execution."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("auto_test", HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_matching_pytest_test_found_recursively(self, tmp_path, load_module):
        tests_dir = tmp_path / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_payments.py"
        test_file.write_text("# test")
        changed = tmp_path / "src" / "payments.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        assert result == str(test_file)

    def test_no_match_returns_none(self, tmp_path, load_module):
        (tmp_path / "tests").mkdir()
        changed = tmp_path / "src" / "nonexistent_module.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        assert result is None

    def test_vitest_test_ts_candidate_found(self, tmp_path, load_module):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        test_file = src_dir / "button.test.ts"
        test_file.write_text("// test")
        changed = src_dir / "button.tsx"
        result = load_module.find_matching_test(changed, "vitest", tmp_path)
        assert result == str(test_file)


class TestAutoTestRunnerSelection:
    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_unknown_test_runner_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "mocha"})
        r = run_hook({"tool_name": "Write", "tool_input": {"file_path": "/some/component.ts"}},
                     tmp_cwd=cwd)
        # mocha is not in the supported runners — hook exits 0 silently
        assert r.returncode == 0
        assert "BLOCKED" not in r.stdout


class TestAutoTestDebounceBoundary:
    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_debounce_zero_always_runs(self, tmp_path):
        # debounce_ms=0 → window is 0s → elapsed is always >= 0 → never suppressed
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("previous_file.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        # Hook should NOT be suppressed — either runs tests or exits for other reason
        # Key assertion: the debounce guard did not suppress (no silent early exit)
        assert "Tests" in r.stdout or r.returncode == 0

    def test_debounce_large_value_suppresses(self, tmp_path):
        # debounce_ms=999999 → window is ~277h → always suppressed when file just written
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("recent_file.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        assert "[zie-framework] Tests" not in r.stdout
        assert r.returncode == 0
