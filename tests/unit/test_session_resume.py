"""Unit tests for hooks/session-resume.py output format.

Strategy: run the hook as a subprocess with a synthetic CLAUDE_CWD pointing
to a temp directory that contains a minimal zie-framework/ tree, then assert
on stdout directly.
"""
import json
import os
import sys
import subprocess
from pathlib import Path

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
        assert "/zie-backlog" in lines[1]

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
        assert lines[3] == "  → Run /zie-status for full state"


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
