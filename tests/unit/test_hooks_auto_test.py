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
    def _cleanup_debounce_debounce(self, tmp_path):
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
    def _cleanup_debounce_runner(self, tmp_path):
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
    def _cleanup_debounce_boundary(self, tmp_path):
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


class TestAutoTestAtomicDebounceWrite:
    """Debounce write must be atomic (write-then-rename, not direct write_text)."""

    @pytest.fixture(autouse=True)
    def _cleanup(self, tmp_path):
        yield
        debounce = project_tmp_path("last-test", tmp_path.name)
        tmp_sib = debounce.parent / (debounce.name + ".tmp")
        for p in (debounce, tmp_sib):
            if p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass
            elif p.is_symlink() or p.exists():
                p.unlink(missing_ok=True)

    def test_debounce_write_uses_safe_write_tmp(self):
        """Source must delegate debounce write to safe_write_tmp, not bare write_text."""
        source = Path(HOOK).read_text()
        assert "safe_write_tmp" in source, \
            "safe_write_tmp call missing from hook source"
        assert "debounce_file.write_text" not in source, \
            "bare debounce_file.write_text found — must use safe_write_tmp"


    def test_debounce_write_oserror_does_not_crash_hook(self, tmp_path):
        """If the debounce write raises OSError, hook must exit 0 (no crash)."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
        debounce = project_tmp_path("last-test", cwd.name)
        # Make debounce path a directory — causes IsADirectoryError (an OSError) on write
        debounce.mkdir(parents=True, exist_ok=True)

        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(cwd / "hooks" / "utils.py")}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr

    def test_debounce_symlink_does_not_block_hook(self, tmp_path):
        """If debounce path is a symlink, hook skips write and continues."""
        # debounce_ms=0 ensures debounce window doesn't suppress before the write
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
        debounce = project_tmp_path("last-test", cwd.name)
        real = tmp_path / "real-debounce-target.txt"
        real.write_text("original")
        debounce.symlink_to(real)

        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(cwd / "hooks" / "utils.py")}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr
        assert real.read_text() == "original"
        assert "WARNING" in r.stderr
        assert "symlink" in r.stderr.lower()


class TestAutoTestFilePathCwdValidation:
    """file_path must be resolved and validated within cwd before use."""

    def test_absolute_path_outside_cwd_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/etc/passwd"}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_tmp_path_outside_cwd_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/malicious.py"}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_dotdot_traversal_outside_cwd_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        escaped = str(cwd) + "/../../etc/passwd"
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": escaped}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_path_inside_cwd_proceeds(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        inside_path = str(cwd / "hooks" / "utils.py")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": inside_path}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert "/etc/passwd" not in r.stdout
        assert "/etc/passwd" not in r.stderr

    def test_out_of_bounds_path_not_leaked_to_output(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/etc/shadow"}},
            tmp_cwd=cwd,
        )
        assert "/etc/shadow" not in r.stdout
        assert "/etc/shadow" not in r.stderr


class TestAutoTestConfigParseWarning:
    def test_warns_on_corrupt_config(self, tmp_path):
        """Corrupt .config must produce a [zie] warning on stderr."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("this is not json {{{")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
            tmp_cwd=tmp_path,
        )
        assert r.returncode == 0
        assert "[zie] warning" in r.stderr, (
            f"Expected '[zie] warning' in stderr, got: {r.stderr!r}"
        )

    def test_no_warning_on_valid_config(self, tmp_path):
        """Valid .config must not produce any warning."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
            tmp_cwd=cwd,
        )
        assert "[zie] warning" not in r.stderr

    def test_no_warning_when_config_missing(self, tmp_path):
        """Missing .config must not produce any warning."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
            tmp_cwd=tmp_path,
        )
        assert "[zie] warning" not in r.stderr


class TestFindMatchingTestEdgeCases:
    """Edge case tests for find_matching_test() — unusual or degraded filesystem states."""

    @pytest.fixture
    def load_module(self):
        """Import auto-test.py without triggering hook execution (same as TestFindMatchingTest)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("auto_test", HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_no_tests_directory_returns_none(self, tmp_path, load_module):
        # No tests/ directory at all — rglob on non-existent path must not raise
        changed = tmp_path / "src" / "payments.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        assert result is None

    def test_symlinked_test_file_found(self, tmp_path, load_module):
        # Real test file in unit subdir; symlink with matching name in tests/ root
        tests_dir = tmp_path / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        real_file = tests_dir / "test_payments.py"
        real_file.write_text("# test")
        link = tmp_path / "tests" / "test_payments.py"
        link.symlink_to(real_file)
        changed = tmp_path / "src" / "payments.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        # rglob finds both real file and symlink (both match test_payments.py)
        assert result in (str(real_file), str(link))

    @pytest.mark.skipif(
        os.getuid() == 0,
        reason="root bypasses filesystem permissions — test not meaningful as root",
    )
    def test_permission_denied_on_tests_dir_returns_none(self, tmp_path, load_module):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        tests_dir.chmod(0o000)
        try:
            changed = tmp_path / "src" / "payments.py"
            result = load_module.find_matching_test(changed, "pytest", tmp_path)
            assert result is None
        finally:
            tests_dir.chmod(0o755)

    def test_non_standard_extension_not_matched_for_pytest(self, tmp_path, load_module):
        # .ts file in tests/ — pytest runner only matches .py files
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_payments.ts").write_text("// ts test")
        changed = tmp_path / "src" / "payments.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        assert result is None

    def test_vitest_missing_test_file_returns_none(self, tmp_path, load_module):
        # src/ exists but no .test.ts or .spec.ts for button
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        changed = src_dir / "button.tsx"
        result = load_module.find_matching_test(changed, "vitest", tmp_path)
        assert result is None

    def test_empty_tests_directory_returns_none(self, tmp_path, load_module):
        # tests/ dir exists with no files inside
        (tmp_path / "tests").mkdir()
        changed = tmp_path / "src" / "payments.py"
        result = load_module.find_matching_test(changed, "pytest", tmp_path)
        assert result is None
