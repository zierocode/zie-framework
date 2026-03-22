"""Tests for hooks/session-resume.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "session-resume.py")

SAMPLE_ROADMAP = """## Now
- [ ] Build the auth module

## Next
- [ ] Add OAuth provider
- [ ] Write integration tests

## Done
- [x] Setup project
"""


def run_hook(tmp_cwd=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    return subprocess.run([sys.executable, HOOK], input=json.dumps({}),
                          capture_output=True, text=True, env=env)


def make_cwd(tmp_path, config=None, roadmap=None, version=None, plans=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    if version:
        (tmp_path / "VERSION").write_text(version)
    if plans:
        plans_dir = zf / "plans"
        plans_dir.mkdir()
        for name, content in plans.items():
            (plans_dir / name).write_text(content)
    return tmp_path


class TestSessionResumeHappyPath:
    def test_prints_project_name(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"project_type": "python-lib"},
                       roadmap=SAMPLE_ROADMAP, version="1.2.3")
        r = run_hook(tmp_cwd=cwd)
        assert tmp_path.name in r.stdout
        assert "[zie-framework]" in r.stdout

    def test_prints_active_feature_from_now_section(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "auth module" in r.stdout

    def test_prints_backlog_count(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "2" in r.stdout  # 2 items in Next

    def test_prints_active_plan_when_present(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP,
                       plans={"2026-03-22-my-feature.md": "# plan"})
        r = run_hook(tmp_cwd=cwd)
        assert "2026-03-22-my-feature.md" in r.stdout

    def test_brain_enabled_when_config_says_so(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"zie_memory_enabled": True}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "enabled" in r.stdout


class TestSessionResumeGracefulDegradation:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_active_feature_message_when_now_empty(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] something\n"
        cwd = make_cwd(tmp_path, config={}, roadmap=roadmap)
        r = run_hook(tmp_cwd=cwd)
        assert "No active feature" in r.stdout or "/zie-backlog" in r.stdout

    def test_handles_missing_roadmap_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # no roadmap
        r = run_hook(tmp_cwd=cwd)
        assert r.returncode == 0
        assert "[zie-framework]" in r.stdout
