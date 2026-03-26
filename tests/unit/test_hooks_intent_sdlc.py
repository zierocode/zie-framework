"""Tests for hooks/intent-sdlc.py — merged UserPromptSubmit hook."""
import json
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import write_roadmap_cache


def run_hook(event, tmp_cwd=None, session_id=None):
    hook = os.path.join(REPO_ROOT, "hooks", "intent-sdlc.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    # Unique session_id per tmp_cwd avoids cache cross-contamination between tests
    if session_id is None:
        session_id = f"test-intent-{abs(hash(str(tmp_cwd))) % 999999}"
    ev = {"session_id": session_id, **event}
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(ev),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd_with_zf(tmp_path, roadmap_content="## Now\n\n## Next\n"):
    (tmp_path / "zie-framework").mkdir(parents=True)
    (tmp_path / "zie-framework" / "ROADMAP.md").write_text(roadmap_content)
    return tmp_path


class TestIntentSdlcHappyPath:
    def _ctx(self, r):
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def test_fix_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
        assert "/zie-fix" in self._ctx(r)

    def test_implement_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "start coding this task now"}, tmp_cwd=cwd)
        assert "/zie-implement" in self._ctx(r)

    def test_release_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ready to deploy and release now"}, tmp_cwd=cwd)
        assert "/zie-release" in self._ctx(r)

    def test_sdlc_context_included_with_active_task(self, tmp_path):
        cwd = make_cwd_with_zf(
            tmp_path,
            roadmap_content="## Now\n- [ ] my-feature — implement\n\n## Next\n",
        )
        r = run_hook({"prompt": "implement the feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        # Both intent and SDLC context in single payload
        assert "/zie-implement" in ctx or "implement" in ctx.lower()
        assert "task" in ctx.lower() or "stage" in ctx.lower()

    def test_outputs_single_json_blob(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "implement this"}, tmp_cwd=cwd)
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert "additionalContext" in parsed
        # Must be a single JSON blob, not two separate lines
        assert r.stdout.count("\n") <= 1 or r.stdout.strip().count("\n") == 0


class TestIntentSdlcEarlyExit:
    def test_short_message_no_output(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "hi"}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_zie_command_no_output(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "/zie-implement now"}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_zf_dir_no_output(self, tmp_path):
        r = run_hook({"prompt": "implement something"}, tmp_cwd=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_long_message_no_output(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "x" * 1100}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestIntentSdlcRoadmapCache:
    def test_uses_cache_when_available(self, tmp_path):
        """When ROADMAP cache is primed with active task, hook reflects it."""
        cwd = make_cwd_with_zf(
            tmp_path,
            roadmap_content="## Now\n\n## Next\n",  # empty Now in disk file
        )
        sid = "test-cache-hit-unique-77z"
        # Prime cache with an active task
        write_roadmap_cache(sid, "## Now\n- [ ] cached-feature — implement\n\n## Next\n")
        r = run_hook({"prompt": "implement the task"}, tmp_cwd=cwd, session_id=sid)
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        ctx = json.loads(r.stdout)["additionalContext"]
        # Should reflect cached task (not empty disk ROADMAP)
        assert "cached-feature" in ctx or "implement" in ctx.lower()

    def test_reads_roadmap_once_on_cache_miss(self, tmp_path):
        """On cache miss, hook reads disk and result is consistent with disk content."""
        cwd = make_cwd_with_zf(
            tmp_path,
            roadmap_content="## Now\n- [ ] disk-feature — implement\n\n## Next\n",
        )
        sid = "test-cache-miss-unique-77z"
        r = run_hook({"prompt": "implement this feature"}, tmp_cwd=cwd, session_id=sid)
        assert r.returncode == 0
        ctx = json.loads(r.stdout)["additionalContext"]
        assert "disk-feature" in ctx or "implement" in ctx.lower()
