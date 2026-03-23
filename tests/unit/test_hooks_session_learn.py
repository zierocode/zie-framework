"""Tests for hooks/session-learn.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "session-learn.py")

SAMPLE_ROADMAP = """## Now
- [ ] Implement login flow
- [ ] Add JWT validation

## Next
- [ ] Add refresh tokens
"""


def run_hook(tmp_cwd, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "CLAUDE_CWD": str(tmp_cwd)}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, HOOK], input=json.dumps({}),
                          capture_output=True, text=True, env=env)


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


class TestSessionLearnPendingLearnFile:
    def test_writes_pending_learn_file(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        assert pending.exists(), f"pending_learn.txt not written at {pending}"

    def test_pending_learn_contains_project_name(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert f"project={tmp_path.name}" in content

    def test_pending_learn_contains_wip_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert "login flow" in content or "wip=" in content

    def test_pending_learn_empty_wip_when_no_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert "project=" in content
        assert "wip=" in content

    def test_no_tmp_file_left_after_write(self, tmp_path):
        """atomic_write must not leave a .tmp sibling file."""
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        tmp_file = pending.with_suffix(".tmp")
        assert not tmp_file.exists(), f".tmp file left behind at {tmp_file}"

    def test_uses_atomic_write(self):
        """session-learn.py must call atomic_write, not write_text directly."""
        source = Path(HOOK).read_text()
        assert "atomic_write" in source, "session-learn.py must use atomic_write"
        assert "pending_learn_file.write_text" not in source, (
            "pending_learn_file.write_text must be replaced by atomic_write"
        )


class TestSessionLearnGuardrails:
    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_path)
        assert r.returncode == 0

    def test_no_crash_when_api_url_unreachable(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "http://localhost:19999",
        })
        assert r.returncode == 0  # must never crash

    def test_skips_api_call_without_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(cwd)  # ZIE_MEMORY_API_KEY="" by default
        assert r.returncode == 0
        assert r.stdout.strip() == ""  # no output when key absent


class TestSessionLearnUrlSafety:
    def test_exits_zero_with_http_scheme_url(self, tmp_path):
        """Non-https URL must cause clean exit before any HTTP call."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        env = {
            **os.environ,
            "CLAUDE_CWD": str(tmp_path),
            "ZIE_MEMORY_API_KEY": "testkey",
            "ZIE_MEMORY_API_URL": "http://evil.example.com",
        }
        hook = os.path.join(REPO_ROOT, "hooks", "session-learn.py")
        r = subprocess.run(
            [sys.executable, hook],
            input=json.dumps({}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""
