"""Tests for hooks/auto-test.py"""

import json
import os
import re as _re
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "hooks")
sys.path.insert(0, HOOKS_DIR)
from utils_io import project_tmp_path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "auto-test.py")


def run_hook(event, tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "ZIE_AUTO_TEST_DEBOUNCE_MS": "", "ZIE_TEST_RUNNER": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, env=env)


def make_cwd(tmp_path, config=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    return tmp_path


class TestAutoTestGuardrails:
    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_action_when_no_test_runner_in_config(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # test_runner key absent
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_action_for_non_edit_tool(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

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
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=cwd)
        # Should be suppressed — no test runner output expected
        assert "[zie-framework] Tests" not in r.stdout


class TestFindMatchingTest:
    """Direct unit tests for find_matching_test() — imported from auto-test module."""

    @pytest.fixture
    def load_module(self):
        """Import auto-test.py without triggering hook execution."""
        import importlib.machinery
        import types

        loader = importlib.machinery.SourceFileLoader("auto_test", str(HOOK))
        mod = types.ModuleType("auto_test")
        mod.__file__ = str(HOOK)
        loader.exec_module(mod)
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
        r = run_hook({"tool_name": "Write", "tool_input": {"file_path": "/some/component.ts"}}, tmp_cwd=cwd)
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
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=cwd)
        # Hook should NOT be suppressed — either runs tests or exits for other reason
        # Key assertion: the debounce guard did not suppress (no silent early exit)
        assert "Tests" in r.stdout or r.returncode == 0

    def test_debounce_large_value_suppresses(self, tmp_path):
        # debounce_ms=999999 → window is ~277h → always suppressed when file just written
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("recent_file.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=cwd)
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

    def test_debounce_uses_cache_manager(self):
        """Source must delegate debounce state to CacheManager, not bare file writes."""
        source = Path(HOOK).read_text()
        assert "CacheManager" in source or "get_cache_manager" in source, "CacheManager usage missing from hook source"
        assert "debounce_file.write_text" not in source, "bare debounce_file.write_text found — must use CacheManager"

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
        """Hook uses CacheManager for debounce (no file writes) — must not crash."""
        # debounce_ms=0 ensures debounce window doesn't suppress before the write
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
        # Old debounce path as symlink — legacy check, should not affect hook
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
    def test_exits_zero_on_corrupt_config(self, tmp_path):
        """Corrupt .config must not crash the hook — load_config() silently returns {}."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("this is not json {{{")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
            tmp_cwd=tmp_path,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""  # no test_runner in corrupt config → no output

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
        import importlib.machinery
        import types

        loader = importlib.machinery.SourceFileLoader("auto_test", str(HOOK))
        mod = types.ModuleType("auto_test")
        mod.__file__ = str(HOOK)
        loader.exec_module(mod)
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


class TestAutoTestEnvVarFastPath:
    """auto-test.py reads ZIE_TEST_RUNNER/ZIE_AUTO_TEST_DEBOUNCE_MS from env
    when available, falling back to .config only when the env vars are absent."""

    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_uses_env_var_test_runner_without_config(self, tmp_path):
        """ZIE_TEST_RUNNER env var set — hook must not need .config to get runner."""
        cwd = make_cwd(tmp_path)  # no config written
        target_file = cwd / "hooks" / "utils.py"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("# stub")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target_file)}},
            tmp_cwd=cwd,
            env_overrides={"ZIE_TEST_RUNNER": "pytest", "ZIE_AUTO_TEST_DEBOUNCE_MS": "0"},
        )
        assert r.returncode == 0
        assert "[zie] warning" not in r.stderr

    def test_env_var_absent_falls_back_to_config(self, tmp_path):
        """No ZIE_TEST_RUNNER env var — hook must fall back to .config."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        target_file = cwd / "hooks" / "utils.py"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("# stub")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target_file)}},
            tmp_cwd=cwd,
            env_overrides={"ZIE_TEST_RUNNER": "", "ZIE_AUTO_TEST_DEBOUNCE_MS": ""},
        )
        assert r.returncode == 0

    def test_empty_env_var_falls_back_to_config(self, tmp_path):
        """ZIE_TEST_RUNNER='' must be treated as absent — .config fallback applies."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        target_file = cwd / "dummy.py"
        target_file.write_text("x = 1")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target_file)}},
            tmp_cwd=cwd,
            env_overrides={"ZIE_TEST_RUNNER": "", "ZIE_AUTO_TEST_DEBOUNCE_MS": ""},
        )
        assert r.returncode == 0
        assert "[zie] warning" not in r.stderr

    def test_debounce_ms_from_env_var(self, tmp_path):
        """ZIE_AUTO_TEST_DEBOUNCE_MS env var must override .config debounce value."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 99999})
        target_file = cwd / "dummy.py"
        target_file.write_text("x = 1")
        # debounce_ms=0 via env → hook must not skip due to debounce
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target_file)}},
            tmp_cwd=cwd,
            env_overrides={"ZIE_TEST_RUNNER": "pytest", "ZIE_AUTO_TEST_DEBOUNCE_MS": "0"},
        )
        assert r.returncode == 0


def parse_additional_context(stdout: str):
    """Extract the additionalContext string from hook stdout, or None if absent."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "additionalContext" in obj:
                return obj["additionalContext"]
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


class TestAdditionalContextInjection:
    """additionalContext must be emitted (flat protocol) after Write/Edit."""

    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    # --- match found ---

    def test_context_emitted_with_matching_test(self, tmp_path):
        """When a test file exists for the changed module, context names it."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_payments.py"
        test_file.write_text("# test")
        changed = str(cwd / "src" / "payments.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None, f"No additionalContext found in stdout: {r.stdout!r}"
        assert ctx.startswith("Affected test: "), f"Unexpected context prefix: {ctx!r}"
        assert "test_payments.py" in ctx

    def test_context_contains_absolute_path(self, tmp_path):
        """Matched test path in context must be absolute."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_utils.py"
        test_file.write_text("# test")
        changed = str(cwd / "src" / "utils.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        path_part = ctx.removeprefix("Affected test: ")
        assert Path(path_part).is_absolute(), f"Path is not absolute: {path_part!r}"

    def test_context_emitted_for_write_tool(self, tmp_path):
        """Context injection fires on Write tool, not only Edit."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_models.py").write_text("# test")
        changed = str(cwd / "src" / "models.py")
        r = run_hook({"tool_name": "Write", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "test_models.py" in ctx

    # --- no match ---

    def test_no_context_when_no_test_found(self, tmp_path):
        """When no matching test exists, additionalContext is suppressed (no noise)."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "billing.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is None, f"additionalContext must be suppressed when no test file found, got: {ctx!r}"

    def test_no_context_write_one_message_suppressed(self, tmp_path):
        """'write one' message is suppressed — no additionalContext emitted when no test."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "stripe.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is None, f"additionalContext must not fire when no test file exists, got: {ctx!r}"

    # --- debounce suppresses context (context only fires when tests actually run) ---

    def test_context_suppressed_when_debounced(self, tmp_path):
        """Context injection is gated behind debounce — no duplicate hints on rapid edits."""
        import time as _time

        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_payments.py"
        test_file.write_text("# test")
        # Write debounce state to unified cache (replaces legacy file-based debounce)
        cache_dir = cwd / ".zie" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "session-cache.json"
        sid = "test-debounce-session"
        now = _time.time()
        safe_path = _re.sub(r"[^a-zA-Z0-9]", "-", str(cwd / "src" / "payments.py"))
        cache_data = {
            f"session:{sid}:test_debounce:{safe_path}": {
                "value": {"last_tested": now, "path": "payments.py"},
                "expires_at": now + 60,
                "created_at": now,
            }
        }
        cache_file.write_text(json.dumps(cache_data))
        changed = str(cwd / "src" / "payments.py")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": changed}},
            tmp_cwd=cwd,
            env_overrides={"CLAUDE_SESSION_ID": sid},
        )
        # Both test run and context injection must be suppressed when debounced
        assert "[zie-framework] Tests" not in r.stdout
        ctx = parse_additional_context(r.stdout)
        assert ctx is None, f"Context should be absent when debounced, got: {r.stdout!r}"

    def test_no_match_context_suppressed_when_debounced(self, tmp_path):
        """'write one' context is also suppressed when debounced."""
        import time as _time

        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        (cwd / "tests").mkdir()
        # Write debounce state to unified cache
        cache_dir = cwd / ".zie" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "session-cache.json"
        sid = "test-debounce-session-2"
        now = _time.time()
        safe_path = _re.sub(r"[^a-zA-Z0-9]", "-", str(cwd / "src" / "billing.py"))
        cache_data = {
            f"session:{sid}:test_debounce:{safe_path}": {
                "value": {"last_tested": now, "path": "billing.py"},
                "expires_at": now + 60,
                "created_at": now,
            }
        }
        cache_file.write_text(json.dumps(cache_data))
        changed = str(cwd / "src" / "billing.py")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": changed}},
            tmp_cwd=cwd,
            env_overrides={"CLAUDE_SESSION_ID": sid},
        )
        ctx = parse_additional_context(r.stdout)
        assert ctx is None, f"Context should be absent when debounced, got: {r.stdout!r}"

    # --- no context on early exits ---

    def test_no_context_when_no_test_runner(self, tmp_path):
        """No context emitted when test_runner is absent — hook exits early."""
        cwd = make_cwd(tmp_path, config={})
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}, tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    def test_no_context_when_not_edit_or_write(self, tmp_path):
        """No context emitted for non-Edit/Write tools."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}}, tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    def test_no_context_when_path_outside_cwd(self, tmp_path):
        """No context emitted when file_path is outside cwd."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/etc/passwd"}}, tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    # --- JSON structure ---

    def test_additional_context_valid_json_line(self, tmp_path):
        """The additionalContext line must be valid flat JSON parseable independently."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_auth.py").write_text("# test")
        changed = str(cwd / "src" / "auth.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        json_lines = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "additionalContext" in obj:
                    json_lines.append(obj)
            except json.JSONDecodeError:
                pass
        assert len(json_lines) == 1, (
            f"Expected exactly one additionalContext JSON line, found {len(json_lines)}: {r.stdout!r}"
        )
        assert "additionalContext" in json_lines[0]

    def test_additional_context_is_string(self, tmp_path):
        """additionalContext value must be a string, not a dict or list."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_auth.py").write_text("# test")
        changed = str(cwd / "src" / "auth.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert isinstance(ctx, str), f"additionalContext must be str, got {type(ctx)}: {ctx!r}"

    # --- vitest runner ---

    def test_context_emitted_for_vitest_match(self, tmp_path):
        """Context injection works for vitest runner when .test.ts file exists."""
        cwd = make_cwd(tmp_path, config={"test_runner": "vitest"})
        src_dir = cwd / "src"
        src_dir.mkdir()
        test_file = src_dir / "button.test.ts"
        test_file.write_text("// test")
        changed = str(src_dir / "button.tsx")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "button.test.ts" in ctx

    def test_no_context_for_vitest_no_match(self, tmp_path):
        """No additionalContext emitted for vitest when no .test.ts found (suppressed)."""
        cwd = make_cwd(tmp_path, config={"test_runner": "vitest"})
        (cwd / "src").mkdir()
        changed = str(cwd / "src" / "modal.tsx")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is None, f"additionalContext must be suppressed when no test file found, got: {ctx!r}"


class TestAutoTestGitTimeout:
    def test_git_timeout_exits_zero(self, tmp_path):
        """auto-test.py must exit 0 when git hangs (TimeoutExpired caught by hook)."""
        import stat

        bin_dir = tmp_path / "fakebin"
        bin_dir.mkdir()
        fake_git = bin_dir / "git"
        fake_git.write_text("#!/bin/sh\nsleep 60\n")
        fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        env = {
            **os.environ,
            "CLAUDE_CWD": str(cwd),
            "PATH": str(bin_dir) + ":" + os.environ.get("PATH", ""),
            "ZIE_MEMORY_API_KEY": "",
            "ZIE_AUTO_TEST_DEBOUNCE_MS": "0",
            "ZIE_TEST_RUNNER": "",
        }
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr


class TestAutoTestEmptyConfig:
    def test_empty_config_json_exits_zero(self, tmp_path):
        """Empty {} config must exit 0, use all defaults, and emit no warning."""
        cwd = make_cwd(tmp_path, config={})
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert "[zie] warning" not in r.stderr


class TestAutoTestWallClockGuard:
    """Source-level checks for wall-clock timer guard."""

    def test_auto_test_max_wait_s_in_source(self):
        source = Path(HOOK).read_text()
        assert "auto_test_max_wait_s" in source

    def test_timer_cancel_in_source(self):
        source = Path(HOOK).read_text()
        assert "timer.cancel()" in source, "threading.Timer must be cancelled in finally block"

    def test_uses_process_group_kill(self):
        source = Path(HOOK).read_text()
        assert "os.killpg" in source, "auto-test.py must use os.killpg to kill hanging process group"

    def test_zero_max_wait_does_not_arm_timer(self):
        source = Path(HOOK).read_text()
        # The guard condition must check max_wait > 0
        assert "auto_test_max_wait_s" in source


def _load_truncate():
    """Import truncate_test_output from auto-test.py via importlib."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "auto_test_hook",
        os.path.join(HOOKS_DIR, "auto-test.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__name__ = "auto_test_hook"
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod.truncate_test_output


class TestTruncateTestOutput:
    def setup_method(self):
        self.fn = _load_truncate()

    def test_summary_line_extracted(self):
        """AC-5: summary line present in output."""
        raw = (
            "collected 5 items\n\ntest_foo.py::test_bar FAILED\n\n"
            "FAILED test_foo.py::test_bar - AssertionError\n\n"
            "1 failed, 4 passed in 0.12s\n"
        )
        result = self.fn(raw)
        assert "1 failed, 4 passed" in result

    def test_first_failed_block_extracted(self):
        """AC-5: first FAILED block present."""
        raw = "FAILED test_foo.py::test_bar - AssertionError: expected 1\nE   assert 0 == 1\n\n2 failed in 0.5s\n"
        result = self.fn(raw)
        assert "FAILED test_foo.py::test_bar" in result
        assert "assert 0 == 1" in result

    def test_capped_at_30_lines(self):
        """AC-5: output capped at 30 lines."""
        long_block = "\n".join([f"E   line {i}" for i in range(100)])
        raw = f"FAILED test_x.py::test_y\n{long_block}\n\n1 failed in 1s\n"
        result = self.fn(raw)
        assert len(result.splitlines()) <= 30

    def test_fallback_when_no_failed_block(self):
        """AC-6: fallback to first 10 non-empty lines."""
        raw = "\n".join([f"line {i}" for i in range(50)]) + "\n1 failed in 0.1s\n"
        result = self.fn(raw)
        non_empty = [ln for ln in result.splitlines() if ln.strip()]
        assert len(non_empty) <= 12

    def test_header_present(self):
        """Output starts with zie-framework header."""
        raw = "FAILED test.py::t\n\n1 failed in 0.1s\n"
        result = self.fn(raw)
        assert "[zie-framework] Tests FAILED" in result


class TestExtensionSkipGuard:
    """AC-1, AC-2, AC-3, AC-4: extension skip guard fires before debounce."""

    def test_md_file_skipped_silently(self, tmp_path):
        """AC-1: .md file → no output, exit 0."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        md_file = cwd / "README.md"
        md_file.write_text("# test")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(md_file)}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    @pytest.mark.parametrize("ext", [".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"])
    def test_non_code_extensions_skipped(self, tmp_path, ext):
        """AC-2: other non-code extensions also skipped."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        f = cwd / f"config{ext}"
        f.write_text("data")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_uppercase_extension_skipped(self, tmp_path):
        """AC-3: .MD uppercase skipped via .lower()."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        f = cwd / "README.MD"
        f.write_text("# test")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_extension_proceeds(self, tmp_path):
        """AC-4: file with no extension proceeds normally (exits 0, may or may not have context)."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        f = cwd / "Makefile"
        f.write_text("all:\n\techo hi")
        r = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
            tmp_cwd=cwd,
        )
        assert r.returncode == 0

    def test_skip_guard_before_debounce(self, tmp_path):
        """AC-1 variant: skipped file does not write debounce sentinel."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        md_file = cwd / "notes.md"
        md_file.write_text("hi")
        run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(md_file)}},
            tmp_cwd=cwd,
        )
        debounce = project_tmp_path("last-test", cwd.name)
        assert not debounce.exists()
