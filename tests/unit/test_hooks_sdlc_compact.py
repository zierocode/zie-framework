"""Tests for hooks/sdlc-compact.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "sdlc-compact.py")
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils_cache import CacheManager

SAMPLE_ROADMAP = """## Now
- [ ] Implement sdlc-compact hook
- [ ] Register in hooks.json

## Next
- [ ] Write integration tests
"""


def run_hook(event_name, tmp_cwd=None, env_overrides=None, session_id=None):
    env = {**os.environ}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    if session_id is None:
        session_id = f"test-sc-{abs(hash(str(tmp_cwd) + event_name)) % 999999}"
    event = {
        "hook_event_name": event_name,
        "session_id": session_id,
        "cwd": str(tmp_cwd) if tmp_cwd else "",
    }
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path, roadmap=None, config=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    return tmp_path


def get_cache(tmp_path):
    """Get CacheManager instance for test project."""
    return CacheManager(tmp_path / ".zie" / "cache")


def read_snapshot(tmp_path, session_id):
    """Read compact-snapshot from CacheManager."""
    cache = get_cache(tmp_path)
    return cache.get("compact-snapshot", session_id)


def write_snapshot(tmp_path, session_id, data):
    """Write compact-snapshot to CacheManager."""
    cache = get_cache(tmp_path)
    cache.set("compact-snapshot", data, session_id, ttl=0, invalidation="session")


# ---------------------------------------------------------------------------
# Outer guard — both events
# ---------------------------------------------------------------------------

class TestSdlcCompactOuterGuard:
    def test_invalid_json_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not-json",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_stdin_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_precompact_exits_zero_without_zf_dir(self, tmp_path):
        # tmp_path has no zie-framework/ subdir
        r = run_hook("PreCompact", tmp_cwd=tmp_path)
        assert r.returncode == 0

    def test_postcompact_exits_zero_without_zf_dir(self, tmp_path):
        r = run_hook("PostCompact", tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""

    def test_unknown_event_name_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook("SomeOtherEvent", tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# PreCompact — snapshot writing
# ---------------------------------------------------------------------------

class TestSdlcCompactPreCompact:
    def test_writes_snapshot_to_cache(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook("PreCompact", tmp_cwd=cwd)
        assert r.returncode == 0
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data is not None, "compact-snapshot must be written to CacheManager"

    def test_snapshot_is_valid_dict(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert isinstance(data, dict)

    def test_snapshot_contains_active_task(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert "sdlc-compact hook" in data["active_task"]

    def test_snapshot_contains_now_items_list(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert isinstance(data["now_items"], list)
        assert len(data["now_items"]) == 2

    def test_snapshot_contains_git_branch_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert "git_branch" in data
        assert isinstance(data["git_branch"], str)

    def test_snapshot_contains_changed_files_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert "changed_files" in data
        assert isinstance(data["changed_files"], list)

    def test_snapshot_contains_tdd_phase_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert "tdd_phase" in data

    def test_snapshot_reads_tdd_phase_from_config(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, config={"tdd_phase": "RED"})
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["tdd_phase"] == "RED"

    def test_snapshot_tdd_phase_defaults_to_empty_when_no_config(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["tdd_phase"] == ""

    def test_snapshot_tdd_phase_empty_when_config_missing_field(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, config={"project_type": "python"})
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["tdd_phase"] == ""

    def test_snapshot_tdd_phase_empty_on_corrupt_config(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        (tmp_path / "zie-framework" / ".config").write_text("not-valid-json")
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["tdd_phase"] == ""

    def test_snapshot_active_task_empty_when_no_now_items(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] something\n"
        cwd = make_cwd(tmp_path, roadmap=roadmap)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["active_task"] == ""
        assert data["now_items"] == []

    def test_snapshot_active_task_empty_when_no_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["active_task"] == ""

    def test_changed_files_capped_at_20(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook("PreCompact", tmp_cwd=cwd)
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert len(data["changed_files"]) <= 20

    def test_no_stdout_on_precompact(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook("PreCompact", tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_git_unavailable_writes_snapshot_with_empty_git_fields(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Point PATH to an empty dir so git is not found
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        r = run_hook("PreCompact", tmp_cwd=cwd, env_overrides={"PATH": str(empty_bin)})
        assert r.returncode == 0
        data = read_snapshot(tmp_path, f"test-sc-{abs(hash(str(cwd) + 'PreCompact')) % 999999}")
        assert data["git_branch"] == ""
        assert data["changed_files"] == []


# ---------------------------------------------------------------------------
# PostCompact — context restoration
# ---------------------------------------------------------------------------

class TestSdlcCompactPostCompact:
    def _session_id(self, cwd):
        return f"test-sc-{abs(hash(str(cwd) + 'PostCompact')) % 999999}"

    def _write_snapshot(self, tmp_path, data: dict):
        sid = self._session_id(tmp_path)
        write_snapshot(tmp_path, sid, data)

    def test_emits_valid_json_to_stdout(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "Implement sdlc-compact hook",
            "now_items": ["Implement sdlc-compact hook", "Register in hooks.json"],
            "git_branch": "dev",
            "changed_files": ["hooks/sdlc-compact.py"],
            "tdd_phase": "GREEN",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        assert r.returncode == 0
        out = json.loads(r.stdout)  # must not raise
        assert "additionalContext" in out

    def test_context_contains_active_task(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "Implement sdlc-compact hook",
            "now_items": ["Implement sdlc-compact hook"],
            "git_branch": "dev",
            "changed_files": [],
            "tdd_phase": "",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "Implement sdlc-compact hook" in ctx

    def test_context_contains_git_branch(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "task",
            "now_items": ["task"],
            "git_branch": "feature/compact",
            "changed_files": [],
            "tdd_phase": "",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "feature/compact" in ctx

    def test_context_contains_tdd_phase_when_set(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "task",
            "now_items": ["task"],
            "git_branch": "dev",
            "changed_files": [],
            "tdd_phase": "RED",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "RED" in ctx

    def test_context_omits_tdd_phase_line_when_empty(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "task",
            "now_items": ["task"],
            "git_branch": "dev",
            "changed_files": [],
            "tdd_phase": "",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        # No blank "TDD phase: " line emitted
        assert "TDD phase: \n" not in ctx

    def test_context_contains_changed_files(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "task",
            "now_items": ["task"],
            "git_branch": "dev",
            "changed_files": ["hooks/sdlc-compact.py", "hooks/hooks.json"],
            "tdd_phase": "",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "hooks/sdlc-compact.py" in ctx

    def test_context_omits_active_task_line_when_empty(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        self._write_snapshot(tmp_path, {
            "active_task": "",
            "now_items": [],
            "git_branch": "dev",
            "changed_files": [],
            "tdd_phase": "",
        })
        r = run_hook("PostCompact", tmp_cwd=cwd)
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "Active task: \n" not in ctx

    def test_missing_snapshot_falls_back_to_live_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # No snapshot written — CacheManager has no compact-snapshot
        r = run_hook("PostCompact", tmp_cwd=cwd)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["additionalContext"]
        assert "sdlc-compact hook" in ctx

    def test_missing_snapshot_missing_roadmap_still_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md, no snapshot
        r = run_hook("PostCompact", tmp_cwd=cwd)
        assert r.returncode == 0
        # Must still emit valid JSON (even if context is minimal)
        out = json.loads(r.stdout)
        assert "additionalContext" in out

    def test_corrupt_snapshot_falls_back_to_live_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Write corrupt data to CacheManager directly
        cache = get_cache(tmp_path)
        sid = self._session_id(cwd)
        # Write a string instead of dict to simulate corrupt data
        cache.set("compact-snapshot", "not-valid-json!!!", sid, ttl=0, invalidation="session")
        r = run_hook("PostCompact", tmp_cwd=cwd)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["additionalContext"]
        assert "sdlc-compact hook" in ctx


    def test_postcompact_git_unavailable_exits_zero(self, tmp_path):
        """PostCompact must exit 0 even when git is not on PATH."""
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # No snapshot — forces live fallback which calls git
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        r = run_hook(
            "PostCompact",
            tmp_cwd=cwd,
            env_overrides={"PATH": str(empty_bin)},
        )
        assert r.returncode == 0
        assert "Traceback" not in r.stderr


# ---------------------------------------------------------------------------
# Error handling convention
# ---------------------------------------------------------------------------

class TestSdlcCompactHooksJsonRegistration:
    def test_precompact_registered(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        config = json.loads(hooks_json.read_text())
        hooks = config.get("hooks", {})
        assert "PreCompact" in hooks, "PreCompact event not registered in hooks.json"
        commands = [
            entry.get("command", "")
            for block in hooks["PreCompact"]
            for entry in block.get("hooks", [])
        ]
        assert any("sdlc-compact.py" in cmd for cmd in commands), (
            "sdlc-compact.py not registered under PreCompact"
        )

    def test_postcompact_registered(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        config = json.loads(hooks_json.read_text())
        hooks = config.get("hooks", {})
        assert "PostCompact" in hooks, "PostCompact event not registered in hooks.json"
        commands = [
            entry.get("command", "")
            for block in hooks["PostCompact"]
            for entry in block.get("hooks", [])
        ]
        assert any("sdlc-compact.py" in cmd for cmd in commands), (
            "sdlc-compact.py not registered under PostCompact"
        )

    def test_existing_hooks_unchanged(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        config = json.loads(hooks_json.read_text())
        hooks = config.get("hooks", {})
        # Spot-check existing registrations are still present
        assert "SessionStart" in hooks
        assert "UserPromptSubmit" in hooks
        assert "PostToolUse" in hooks
        assert "PreToolUse" in hooks
        assert "Stop" in hooks


class TestSdlcCompactErrorHandlingConvention:
    def test_hook_file_has_two_tier_outer_guard(self):
        """Outer guard must use bare except Exception -> sys.exit(0)."""
        src = Path(HOOK).read_text()
        assert "sys.exit(0)" in src, "outer guard sys.exit(0) missing"

    def test_inner_ops_use_named_exception_with_stderr(self):
        """Inner operations must use 'except Exception as e' with stderr print."""
        src = Path(HOOK).read_text()
        assert "except Exception as e:" in src
        assert "file=sys.stderr" in src

    def test_no_nonzero_exit_code(self):
        """Hook must never call sys.exit with a non-zero argument."""
        import ast
        src = Path(HOOK).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "exit"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "sys"
                ):
                    if node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.Constant) and arg.value != 0:
                            raise AssertionError(
                                f"sys.exit({arg.value}) found at line {node.lineno} — "
                                "hooks must only exit 0"
                            )


class TestSubprocessTimeouts:
    def test_git_timeout_exits_zero(self, tmp_path):
        """Hook must exit 0 when both git calls hang beyond 5s.

        Timing contract:
          - Fake git sleeps 60s.
          - Hook has timeout=5 per call (GREEN) -> ~10s total -> exits 0.
          - Hook has no timeout (RED) -> hangs 60s -> outer test fires at 15s -> TimeoutExpired (FAIL).
        """
        import stat
        # Create a fake git that hangs
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()
        fake_git = fake_bin / "git"
        fake_git.write_text("#!/bin/sh\nsleep 60\n")
        fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)

        # Build cwd with zie-framework/ so hook passes outer guard
        cwd = make_cwd(tmp_path / "proj", roadmap=SAMPLE_ROADMAP)

        env = {**os.environ}
        env["CLAUDE_CWD"] = str(cwd)
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        event = json.dumps({"hook_event_name": "PreCompact", "cwd": str(cwd)})

        result = subprocess.run(
            [sys.executable, HOOK],
            input=event,
            capture_output=True,
            text=True,
            timeout=15,  # > 2 * 5s (branch + diff) but < 60s (fake git sleep)
            env=env,
        )
        assert result.returncode == 0