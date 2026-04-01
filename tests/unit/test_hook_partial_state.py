"""
Error-path tests: hooks must exit 0 when project state is present but partial/empty.
Validates graceful degradation when standard subdirs/files are absent.
"""

import pytest


def _base_zf(tmp_path):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    return tmp_path, zf


@pytest.mark.error_path
def test_roadmap_empty_now_section(tmp_path, run_hook):
    """ROADMAP.md exists but ## Now section is empty — hooks must not crash."""
    cwd, zf = _base_zf(tmp_path)
    (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n- next item\n")
    r = run_hook("intent-sdlc.py", {"prompt": "check status"}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_specs_dir_missing(tmp_path, run_hook):
    """specs/ dir absent — subagent-context.py must inject default context, not fail."""
    cwd, zf = _base_zf(tmp_path)
    (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
    # No zf/specs/ directory
    r = run_hook("subagent-context.py", {"agent_type": "Plan"}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_plans_dir_missing(tmp_path, run_hook):
    """plans/ dir absent — subagent-context.py must inject default context, not fail."""
    cwd, zf = _base_zf(tmp_path)
    (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
    (zf / "specs").mkdir()
    # No zf/plans/ directory
    r = run_hook("subagent-context.py", {"agent_type": "Explore"}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_project_md_missing(tmp_path, run_hook):
    """PROJECT.md absent — session-resume.py must exit 0 without injecting stale context."""
    cwd, zf = _base_zf(tmp_path)
    (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
    # No zf/PROJECT.md
    r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
    assert r.returncode == 0
