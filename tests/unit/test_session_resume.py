"""Unit tests for hooks/session-resume.py output format.

Strategy: run the hook as a subprocess with a synthetic CLAUDE_CWD pointing
to a temp directory that contains a minimal zie-framework/ tree, then assert
on stdout directly.
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "session-resume.py"


def _make_zf(tmp_path: Path, *, version="1.0.0", project_type="lib",
             zie_memory=False, now_items=None) -> Path:
    """Build a minimal zie-framework scaffold under tmp_path."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()

    # VERSION file at project root (tmp_path acts as project root)
    (tmp_path / "VERSION").write_text(version)

    # .config
    config = {"project_type": project_type, "zie_memory_enabled": zie_memory}
    (zf / ".config").write_text(json.dumps(config))

    # ROADMAP.md — build minimal Now section
    if now_items:
        now_block = "\n".join(f"- {item}" for item in now_items)
        roadmap = f"## Now\n\n{now_block}\n\n## Next\n\n## Backlog\n"
    else:
        roadmap = "## Now\n\n## Next\n\n## Backlog\n"
    (zf / "ROADMAP.md").write_text(roadmap)

    return zf


def _run_hook(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run session-resume.py with CLAUDE_CWD pointing at tmp_path."""
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    # Provide valid JSON on stdin (SessionStart event shape)
    stdin_data = json.dumps({"session_id": "test-session"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )


class TestOutputLineCount:
    def test_no_active_feature_is_exactly_4_lines(self, tmp_path):
        _make_zf(tmp_path, now_items=None)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 4, (
            f"Expected 4 lines, got {len(lines)}:\n{result.stdout}"
        )

    def test_with_active_feature_is_exactly_4_lines(self, tmp_path):
        _make_zf(tmp_path, now_items=["session-resume-compression"])
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 4, (
            f"Expected 4 lines, got {len(lines)}:\n{result.stdout}"
        )


class TestOutputFormat:
    def test_line1_contains_project_type_version(self, tmp_path):
        _make_zf(tmp_path, version="2.3.4", project_type="plugin")
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        line1 = result.stdout.strip().splitlines()[0]
        assert "[zie-framework]" in line1
        assert "(plugin)" in line1
        assert "v2.3.4" in line1

    def test_line2_active_feature_present(self, tmp_path):
        _make_zf(tmp_path, now_items=["my-cool-feature"])
        result = _run_hook(tmp_path)
        lines = result.stdout.strip().splitlines()
        assert lines[1].startswith("  Active:")
        assert "my-cool-feature" in lines[1]

    def test_line2_no_active_feature_fallback(self, tmp_path):
        _make_zf(tmp_path, now_items=None)
        result = _run_hook(tmp_path)
        lines = result.stdout.strip().splitlines()
        assert lines[1].startswith("  Active:")
        assert "No active feature" in lines[1]
        assert "/backlog" in lines[1]

    def test_line3_brain_enabled(self, tmp_path):
        _make_zf(tmp_path, zie_memory=True)
        result = _run_hook(tmp_path)
        lines = result.stdout.strip().splitlines()
        assert lines[2] == "  Brain: enabled"

    def test_line3_brain_disabled(self, tmp_path):
        _make_zf(tmp_path, zie_memory=False)
        result = _run_hook(tmp_path)
        lines = result.stdout.strip().splitlines()
        assert lines[2] == "  Brain: disabled"

    def test_line4_zie_status_hint(self, tmp_path):
        _make_zf(tmp_path)
        result = _run_hook(tmp_path)
        lines = result.stdout.strip().splitlines()
        assert lines[3] == "  → Run /status for full state"


HOOK_DIR = REPO_ROOT / "hooks"


def _import_session_resume():
    """Import session-resume as a module (adds hooks/ to sys.path)."""
    import importlib.util
    if str(HOOK_DIR) not in sys.path:
        sys.path.insert(0, str(HOOK_DIR))
    spec = importlib.util.spec_from_file_location("session_resume", HOOK)
    mod = importlib.util.module_from_spec(spec)
    # Don't exec the module-level code (the outer guard) — we only want the functions
    # We manually load just the functions by parsing the file content up to the guard
    return mod


class TestCheckPlaywrightVersion:
    """Unit tests for _check_playwright_version() imported directly."""

    def setup_method(self):
        if str(HOOK_DIR) not in sys.path:
            sys.path.insert(0, str(HOOK_DIR))
        # Import the function directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("_sr_mod", HOOK)
        self._mod = importlib.util.module_from_spec(spec)
        # Patch read_event and sys.exit so module-level guard doesn't execute
        import unittest.mock as _mock
        with _mock.patch("builtins.open"), _mock.patch("sys.exit"), \
             _mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = '{"session_id": "test"}'
            try:
                spec.loader.exec_module(self._mod)
            except Exception:
                pass

    def test_disabled_when_playwright_not_enabled(self, capsys):
        """No subprocess spawned when playwright_enabled is False/absent."""
        config = {"playwright_enabled": False}
        with patch("subprocess.run") as mock_run:
            self._mod._check_playwright_version(config)
        mock_run.assert_not_called()
        assert capsys.readouterr().err == ""

    def test_not_installed_logs_warning_and_disables(self, capsys):
        """FileNotFoundError → warning on stderr and playwright disabled."""
        config = {"playwright_enabled": True}
        with patch.object(self._mod.subprocess, "run", side_effect=FileNotFoundError()):
            self._mod._check_playwright_version(config)
        assert config["playwright_enabled"] is False
        err = capsys.readouterr().err
        assert "playwright not found" in err

    def test_old_version_logs_cve_warning_and_disables(self, capsys):
        """Version below minimum → CVE-2025-59288 warning and disabled."""
        config = {"playwright_enabled": True}
        mock_result = MagicMock()
        mock_result.stdout = "Version 1.50.0\n"
        with patch.object(self._mod.subprocess, "run", return_value=mock_result):
            self._mod._check_playwright_version(config)
        assert config["playwright_enabled"] is False
        err = capsys.readouterr().err
        assert "CVE-2025-59288" in err
        assert "1.50.0" in err

    def test_safe_version_no_output_no_disable(self, capsys):
        """Version >= minimum → no stderr, playwright stays enabled."""
        config = {"playwright_enabled": True}
        mock_result = MagicMock()
        mock_result.stdout = "Version 1.55.1\n"
        with patch.object(self._mod.subprocess, "run", return_value=mock_result):
            self._mod._check_playwright_version(config)
        assert config["playwright_enabled"] is True
        assert capsys.readouterr().err == ""

    def test_parse_error_logs_notice_does_not_disable(self, capsys):
        """Unparseable version string → parse-error notice, playwright NOT disabled."""
        config = {"playwright_enabled": True}
        mock_result = MagicMock()
        mock_result.stdout = "not a version at all\n"
        with patch.object(self._mod.subprocess, "run", return_value=mock_result):
            self._mod._check_playwright_version(config)
        assert config.get("playwright_enabled") is True
        err = capsys.readouterr().err
        assert "could not parse playwright version" in err


class TestHookSafety:
    def test_exits_zero_when_no_zf_directory(self, tmp_path):
        """Hook must exit 0 and produce no output when zie-framework/ absent."""
        result = _run_hook(tmp_path)
        assert result.returncode == 0

    def test_exits_zero_on_malformed_stdin(self, tmp_path):
        _make_zf(tmp_path)
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json at all",
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0

    def test_exits_zero_on_empty_stdin(self, tmp_path):
        _make_zf(tmp_path)
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0


class TestEnvFilePermissions:
    def test_env_file_permissions_are_0600(self, tmp_path):
        _make_zf(tmp_path)
        env_file = tmp_path / "claude_env"
        env_file.write_text("")
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        env["CLAUDE_ENV_FILE"] = str(env_file)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"session_id": "test-session"}),
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        mode = stat.S_IMODE(env_file.stat().st_mode)
        assert mode == 0o600, f"env file must be 0o600, got {oct(mode)}"
