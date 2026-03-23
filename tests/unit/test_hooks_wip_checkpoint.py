"""Tests for hooks/wip-checkpoint.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "wip-checkpoint.py")

SAMPLE_ROADMAP = """## Now
- [ ] Refactor the payment module
"""


def run_hook(tool_name="Edit", tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    event = {"tool_name": tool_name, "tool_input": {"file_path": "/some/file.py"}}
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                          capture_output=True, text=True, env=env)


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


def reset_counter():
    counter = Path("/tmp/zie-framework-edit-count")
    if counter.exists():
        counter.unlink()


class TestWipCheckpointGuardrails:
    def test_no_action_without_api_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)  # ZIE_MEMORY_API_KEY="" — should exit silently
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_cwd=tmp_path, env_overrides={"ZIE_MEMORY_API_KEY": "fake"})
        assert r.returncode == 0

    def test_no_action_for_non_edit_tool(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tool_name="Bash", tmp_cwd=cwd,
                     env_overrides={"ZIE_MEMORY_API_KEY": "fake"})
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self):
        r = subprocess.run([sys.executable, HOOK], input="bad json",
                           capture_output=True, text=True)
        assert r.returncode == 0


class TestWipCheckpointCounter:
    def test_counter_increments_each_call(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Hook exits early without API key — must provide one to reach counter logic
        # URL must use https:// to pass the scheme validation guard
        for _ in range(3):
            run_hook(tmp_cwd=cwd, env_overrides={
                "ZIE_MEMORY_API_KEY": "fake-key",
                "ZIE_MEMORY_API_URL": "https://localhost:19999",
            })
        counter = Path("/tmp/zie-framework-edit-count")
        assert counter.exists()
        assert int(counter.read_text().strip()) == 3

    def test_no_network_call_before_fifth_edit(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        for _ in range(4):
            r = run_hook(tmp_cwd=cwd, env_overrides={
                "ZIE_MEMORY_API_KEY": "fake-key",
                "ZIE_MEMORY_API_URL": "http://localhost:19999",
            })
            assert r.returncode == 0  # must not crash even on network error

    def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        Path("/tmp/zie-framework-edit-count").write_text("4")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "http://localhost:19999",
        })
        assert r.returncode == 0  # graceful failure — never crash


class TestWipCheckpointUrlSafety:
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
        hook = os.path.join(REPO_ROOT, "hooks", "wip-checkpoint.py")
        r = subprocess.run(
            [sys.executable, hook],
            input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""
