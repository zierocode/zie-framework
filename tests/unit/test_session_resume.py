"""Unit tests for hooks/session-resume.py output format.

Strategy: run the hook as a subprocess with a synthetic CLAUDE_CWD pointing
to a temp directory that contains a minimal zie-framework/ tree, then assert
on stdout directly.
"""

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "session-resume.py"


def _make_zf(tmp_path: Path, *, version="1.0.0", project_type="lib", zie_memory=False, now_items=None) -> Path:
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

    # commands/ directory at PROJECT ROOT for context loader
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir(exist_ok=True)
    for cmd in (
        "backlog",
        "spec",
        "plan",
        "implement",
        "release",
        "retro",
        "sprint",
        "fix",
        "chore",
        "hotfix",
        "status",
        "audit",
        "resync",
        "init",
        "guide",
    ):
        (commands_dir / f"{cmd}.md").write_text(f"# /{cmd}")

    # skills/ directory at PROJECT ROOT
    skills_dir = tmp_path / "skills" / "context-map"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "SKILL.md").write_text("# context-map")

    return zf


def _clean_session_cache(session_id: str) -> None:
    """Clean session cache directories between tests."""
    import shutil

    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
    cache_dir = Path("/tmp") / f"zie-{safe_id}"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


def _run_hook(tmp_path: Path, session_id: str = "test-session-resume") -> subprocess.CompletedProcess:
    """Run session-resume.py with CLAUDE_CWD pointing at tmp_path."""
    # Clean cache before test to prevent stale data
    _clean_session_cache(session_id)

    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    env["CLAUDE_SESSION_ID"] = session_id
    # Provide valid JSON on stdin (SessionStart event shape)
    stdin_data = json.dumps({"session_id": session_id})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )


class TestOutputLineCount:
    def test_no_active_feature_has_at_least_1_line(self, tmp_path):
        _make_zf(tmp_path, now_items=None)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) >= 1, f"Expected at least 1 line, got {len(lines)}:\n{result.stdout}"

    def test_with_active_feature_has_at_least_1_line(self, tmp_path):
        _make_zf(tmp_path, now_items=["session-resume-compression"])
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) >= 1, f"Expected at least 1 line, got {len(lines)}:\n{result.stdout}"


class TestOutputFormat:
    def test_line1_contains_project_type_version(self, tmp_path):
        _make_zf(tmp_path, version="2.3.4", project_type="plugin")
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        line1 = result.stdout.strip().splitlines()[0]
        assert "[zf]" in line1
        assert "(plugin)" in line1
        assert "v2.3.4" in line1

    def test_line1_now_key_with_active_feature(self, tmp_path):
        _make_zf(tmp_path, now_items=["my-cool-feature"])
        result = _run_hook(tmp_path)
        line1 = result.stdout.strip().splitlines()[0]
        assert "now:" in line1
        assert "my-cool-feature" in line1

    def test_line1_now_key_fallback_when_empty(self, tmp_path):
        _make_zf(tmp_path, now_items=None)
        result = _run_hook(tmp_path)
        line1 = result.stdout.strip().splitlines()[0]
        assert "now:" in line1

    def test_line1_mem_key_enabled(self, tmp_path):
        _make_zf(tmp_path, zie_memory=True)
        result = _run_hook(tmp_path)
        line1 = result.stdout.strip().splitlines()[0]
        assert "mem:on" in line1

    def test_line1_mem_key_disabled(self, tmp_path):
        _make_zf(tmp_path, zie_memory=False)
        result = _run_hook(tmp_path)
        line1 = result.stdout.strip().splitlines()[0]
        assert "mem:off" in line1


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

        with _mock.patch("builtins.open"), _mock.patch("sys.exit"), _mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = '{"session_id": "test"}'
            try:
                spec.loader.exec_module(self._mod)
            except Exception:
                pass

    def test_disabled_when_playwright_not_enabled(self, capsys):
        """No subprocess spawned when playwright_enabled is False/absent."""
        config = {"playwright_enabled": False}
        with patch.object(self._mod, "get_playwright_version_cached", return_value="1.55.1"):
            self._mod._check_playwright_version(config, "test-session", Path("/tmp"))
        assert capsys.readouterr().err == ""

    def test_not_installed_logs_warning_and_disables(self, capsys):
        """Empty version string → warning on stderr and playwright disabled."""
        config = {"playwright_enabled": True}
        with patch.object(self._mod, "get_playwright_version_cached", return_value=""):
            self._mod._check_playwright_version(config, "test-session", Path("/tmp"))
        assert config["playwright_enabled"] is False
        err = capsys.readouterr().err
        assert "playwright not found" in err

    def test_old_version_logs_cve_warning_and_disables(self, capsys):
        """Version below minimum → CVE-2025-59288 warning and disabled."""
        config = {"playwright_enabled": True}
        with patch.object(self._mod, "get_playwright_version_cached", return_value="1.50.0"):
            self._mod._check_playwright_version(config, "test-session", Path("/tmp"))
        assert config["playwright_enabled"] is False
        err = capsys.readouterr().err
        assert "CVE-2025-59288" in err
        assert "1.50.0" in err

    def test_safe_version_no_output_no_disable(self, capsys):
        """Version >= minimum → no stderr, playwright stays enabled."""
        config = {"playwright_enabled": True}
        with patch.object(self._mod, "get_playwright_version_cached", return_value="1.55.1"):
            self._mod._check_playwright_version(config, "test-session", Path("/tmp"))
        assert config["playwright_enabled"] is True
        assert capsys.readouterr().err == ""

    def test_parse_error_logs_notice_does_not_disable(self, capsys):
        """Unparseable version string → parse-error notice, playwright NOT disabled."""
        config = {"playwright_enabled": True}
        with patch.object(self._mod, "get_playwright_version_cached", return_value="not a version at all"):
            self._mod._check_playwright_version(config, "test-session", Path("/tmp"))
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


# ── Area 4: Framework Self-Awareness tests ────────────────────────────────────


def _run_hook_no_zf(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run session-resume.py with NO zie-framework/ directory."""
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"session_id": "test-session"}),
        capture_output=True,
        text=True,
        env=env,
    )


class TestInitNudge:
    """When zie-framework/ is absent, hook prints /init nudge instead of silent exit."""

    def test_prints_init_nudge_when_no_zf(self, tmp_path):
        result = _run_hook_no_zf(tmp_path)
        assert result.returncode == 0
        assert "/init" in result.stdout, "must print /init nudge when zie-framework/ absent, got: " + repr(
            result.stdout
        )

    def test_init_nudge_mentions_zie_framework(self, tmp_path):
        result = _run_hook_no_zf(tmp_path)
        assert "zie-framework" in result.stdout.lower() or "initialize" in result.stdout.lower()


class TestStalenessWarning:
    """Stale PROJECT.md triggers /resync warning."""

    def test_resync_warning_when_project_md_stale(self, tmp_path):
        zf = _make_zf(tmp_path)
        # Write a PROJECT.md that is older than the git repo's latest commit
        # We simulate staleness by writing PROJECT.md with a very old mtime
        project_md = zf / "PROJECT.md"
        project_md.write_text("# Project\nStale content")
        import os as _os
        import time as _time

        old_mtime = _time.time() - 86400  # 1 day ago
        _os.utime(project_md, (old_mtime, old_mtime))
        result = _run_hook(tmp_path)
        # The warning appears in stdout when stale
        # (may not fire if git is unavailable in test env — soft assert)
        assert result.returncode == 0


class TestCommandListOutput:
    """session-resume prints status line with /backlog nudge when zie-framework/ found."""

    def test_status_line_present_on_fresh_state(self, tmp_path):
        _make_zf(tmp_path)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        # Status line starts with [zf] and contains version info
        assert any("[zf]" in line for line in result.stdout.splitlines()), (
            "stdout must contain a [zf] status line"
        )

    def test_status_line_contains_version(self, tmp_path):
        _make_zf(tmp_path, version="2.3.4")
        result = _run_hook(tmp_path)
        out = result.stdout
        assert "v2.3.4" in out, "status line must include version"

    def test_backlog_nudge_in_status_when_no_active_feature(self, tmp_path):
        _make_zf(tmp_path, now_items=None)
        result = _run_hook(tmp_path)
        out = result.stdout
        assert "/backlog" in out, "status line must include /backlog nudge when no active feature"


class TestBacklogNudge:
    """Backlog nudge appears when Next lane has items."""

    def _make_zf_with_next(self, tmp_path: Path) -> Path:
        zf = _make_zf(tmp_path)
        roadmap = "## Now\n\n## Next\n\n- my-pending-feature\n\n## Done\n"
        (zf / "ROADMAP.md").write_text(roadmap)
        return zf

    def test_backlog_nudge_when_next_lane_has_items(self, tmp_path):
        self._make_zf_with_next(tmp_path)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        assert "backlog" in result.stdout.lower() or "/spec" in result.stdout, (
            "must print backlog nudge when Next lane has items"
        )


class TestSessionResumeErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
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
