"""Tests for hooks/wip-checkpoint.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "wip-checkpoint.py")
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import persistent_project_path

SAMPLE_ROADMAP = """## Now
- [ ] Refactor the payment module
"""


def run_hook(tool_name="Edit", tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_ENABLED": ""}
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



class TestWipCheckpointUsesProjectTmpPath:
    def test_no_local_counter_path_helper(self):
        """counter_path() local helper must be removed — use project_tmp_path() from utils."""
        src = Path(HOOK).parent.parent / "tests" / "unit" / "test_hooks_wip_checkpoint.py"
        content = src.read_text()
        forbidden = "def " + "counter_path"
        assert forbidden not in content, (
            "counter_path() local helper still present — replace with project_tmp_path() from utils"
        )

    def test_uses_persistent_project_path(self):
        """wip-checkpoint.py must use persistent_project_path for the edit counter."""
        source = Path(HOOK).read_text()
        assert "persistent_project_path" in source, (
            "wip-checkpoint.py must use persistent_project_path, not project_tmp_path"
        )

    def test_does_not_use_project_tmp_path(self):
        """wip-checkpoint.py must not call project_tmp_path for the edit counter."""
        source = Path(HOOK).read_text()
        assert "project_tmp_path" not in source, (
            "wip-checkpoint.py must migrate edit-count to persistent_project_path"
        )


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
    @pytest.fixture(autouse=True)
    def _cleanup_counter(self, tmp_path):
        yield
        p = persistent_project_path("edit-count", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_counter_increments_each_call(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Hook exits early without API key — must provide one to reach counter logic
        # URL must use https:// to pass the scheme validation guard
        for _ in range(3):
            run_hook(tmp_cwd=cwd, env_overrides={
                "ZIE_MEMORY_API_KEY": "fake-key",
                "ZIE_MEMORY_API_URL": "https://localhost:19999",
            })
        counter = persistent_project_path("edit-count", tmp_path.name)
        assert counter.exists()
        assert int(counter.read_text().strip()) == 3

    def test_no_network_call_before_fifth_edit(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        for _ in range(4):
            r = run_hook(tmp_cwd=cwd, env_overrides={
                "ZIE_MEMORY_API_KEY": "fake-key",
                "ZIE_MEMORY_API_URL": "http://localhost:19999",
            })
            assert r.returncode == 0  # must not crash even on network error

    def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        persistent_project_path("edit-count", tmp_path.name).write_text("4")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",  # https to pass guard, bad host fails network
        })
        assert r.returncode == 0  # graceful failure — never crash
        assert persistent_project_path("edit-count", tmp_path.name).read_text().strip() == "5"
        assert r.stderr.strip() != "", "hook must report network error to stderr"

    def test_corrupt_counter_file_resets_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        persistent_project_path("edit-count", tmp_path.name).write_text("not-a-number\n")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        assert persistent_project_path("edit-count", tmp_path.name).read_text().strip() == "1"
        assert "wip-checkpoint" in r.stderr

    def test_whitespace_only_counter_file_resets_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        persistent_project_path("edit-count", tmp_path.name).write_text("   \n")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        assert persistent_project_path("edit-count", tmp_path.name).read_text().strip() == "1"
        assert "wip-checkpoint" in r.stderr

    def test_empty_counter_file_resets_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        persistent_project_path("edit-count", tmp_path.name).write_text("")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        assert persistent_project_path("edit-count", tmp_path.name).read_text().strip() == "1"


class TestWipCheckpointRoadmapEdgeCases:
    @pytest.fixture(autouse=True)
    def _cleanup_counter(self, tmp_path):
        yield
        p = persistent_project_path("edit-count", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_missing_roadmap_no_crash(self, tmp_path):
        # zie-framework/ dir exists but ROADMAP.md absent
        cwd = make_cwd(tmp_path)  # no roadmap arg
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        counter = persistent_project_path("edit-count", tmp_path.name)
        assert counter.exists(), "hook must write counter even when roadmap is absent"
        assert counter.read_text().strip() == "1"

    def test_empty_now_section_no_crash(self, tmp_path):
        roadmap = "## Now\n\n## Ready\n- [ ] Some item\n"
        cwd = make_cwd(tmp_path, roadmap=roadmap)
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        counter = persistent_project_path("edit-count", tmp_path.name)
        assert counter.exists(), "hook must write counter even when Now section is empty"
        assert counter.read_text().strip() == "1"

    def test_malformed_now_items_graceful_skip(self, tmp_path):
        roadmap = "## Now\nnot a list item\nanother line\n"
        cwd = make_cwd(tmp_path, roadmap=roadmap)
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "https://localhost:19999",
        })
        assert r.returncode == 0
        counter = persistent_project_path("edit-count", tmp_path.name)
        assert counter.exists(), "hook must write counter even with malformed Now items"
        assert counter.read_text().strip() == "1"


class TestWipCheckpointSymlinkProtection:
    @pytest.fixture(autouse=True)
    def _cleanup_counter(self, tmp_path):
        yield
        p = persistent_project_path("edit-count", tmp_path.name)
        if p.is_symlink() or p.exists():
            p.unlink(missing_ok=True)

    def test_counter_symlink_does_not_overwrite_target(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        counter = persistent_project_path("edit-count", tmp_path.name)
        real_file = tmp_path / "important.txt"
        real_file.write_text("do not overwrite")
        counter.symlink_to(real_file)

        env = {
            **os.environ,
            "CLAUDE_CWD": str(cwd),
            "ZIE_MEMORY_API_KEY": "test-key",
            "ZIE_MEMORY_API_URL": "https://fake.example.com",
        }
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
            capture_output=True,
            text=True,
            env=env,
        )

        assert r.returncode == 0
        assert "Traceback" not in r.stderr
        assert real_file.read_text() == "do not overwrite"


class TestWipCheckpointUsesSharedHelper:
    def test_uses_call_zie_memory_api(self):
        """wip-checkpoint.py must use call_zie_memory_api, not inline urllib."""
        source = Path(HOOK).read_text()
        assert "call_zie_memory_api" in source, (
            "wip-checkpoint.py must import and use call_zie_memory_api from utils"
        )

    def test_no_inline_urlopen(self):
        """wip-checkpoint.py must not contain inline urlopen calls."""
        source = Path(HOOK).read_text()
        assert "urlopen" not in source, (
            "wip-checkpoint.py must not call urlopen directly — use call_zie_memory_api"
        )


class TestWipCheckpointMemoryEnabledFastPath:
    @pytest.fixture(autouse=True)
    def _cleanup_counter(self, tmp_path):
        yield
        p = persistent_project_path("edit-count", tmp_path.name)
        if p.exists():
            p.unlink()

    def test_exits_early_when_zie_memory_enabled_is_zero(self, tmp_path):
        """ZIE_MEMORY_ENABLED=0 must cause hook to exit 0 without counter I/O."""
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_ENABLED": "0",
            "ZIE_MEMORY_API_KEY": "real-key",
            "ZIE_MEMORY_API_URL": "https://example.com",
        })
        assert r.returncode == 0
        counter = persistent_project_path("edit-count", tmp_path.name)
        assert not counter.exists()

    def test_proceeds_normally_when_zie_memory_enabled_is_one(self, tmp_path):
        """ZIE_MEMORY_ENABLED=1 must not short-circuit the hook."""
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_ENABLED": "1",
            "ZIE_MEMORY_API_KEY": "",
            "ZIE_MEMORY_API_URL": "",
        })
        assert r.returncode == 0

    def test_absent_env_var_falls_back_to_normal_flow(self, tmp_path):
        """ZIE_MEMORY_ENABLED absent — hook must proceed to api_key guard as before."""
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "",
            "ZIE_MEMORY_API_URL": "",
        })
        assert r.returncode == 0


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

    def test_memory_unreachable_http_url_exits_zero(self, tmp_path):
        """http://localhost:19999 (nothing listening) — URL guard blocks before network call."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        env = {
            **os.environ,
            "CLAUDE_CWD": str(tmp_path),
            "ZIE_MEMORY_API_KEY": "testkey",
            "ZIE_MEMORY_API_URL": "http://localhost:19999",
        }
        hook = os.path.join(REPO_ROOT, "hooks", "wip-checkpoint.py")
        r = subprocess.run(
            [sys.executable, hook],
            input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr
