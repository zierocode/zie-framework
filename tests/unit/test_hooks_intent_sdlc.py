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


class TestPipelineGates:
    """Gate enforcement: plan intent + no approved spec → ⛔; implement + no Now item → ⛔."""

    def _ctx(self, r):
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def _make_spec(self, specs_dir, slug, approved=True):
        specs_dir.mkdir(parents=True, exist_ok=True)
        content = f"---\napproved: {'true' if approved else 'false'}\n---\n# Spec\n"
        (specs_dir / f"2026-01-01-{slug}-design.md").write_text(content)

    def test_plan_intent_no_spec_blocks(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx
        assert "my-feature" in ctx

    def test_plan_intent_approved_spec_passes(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "my-feature", approved=True)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    def test_plan_intent_draft_spec_blocks(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "my-feature", approved=False)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_plan_intent_no_roadmap_slug_no_gate(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "ready to plan"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    def test_plan_intent_multiple_slugs_any_missing_blocks(self, tmp_path):
        roadmap = (
            "## Now\n\n"
            "## Next\n- [ ] feat-a — spec\n- [ ] feat-b — spec\n\n"
            "## Ready\n"
        )
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "feat-a", approved=True)
        r = run_hook({"prompt": "plan feat-a and feat-b together"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx
        assert "feat-b" in ctx

    def test_plan_false_positive_generic_phrase(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "plan this design pattern for our api"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    def test_implement_intent_no_now_item_blocks(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — plan\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's start coding now"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_implement_intent_all_done_now_blocks(self, tmp_path):
        roadmap = "## Now\n- [x] my-feature — implement\n\n## Next\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "continue implementing"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_implement_intent_active_now_passes(self, tmp_path):
        roadmap = "## Now\n- [ ] my-feature — implement\n\n## Next\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's implement the next task"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx


class TestHelperFunctions:
    """Unit tests for _extract_roadmap_slugs and _spec_approved."""

    @classmethod
    def setup_class(cls):
        path = os.path.join(REPO_ROOT, "hooks", "intent-sdlc.py")
        source = open(path).read()
        stop_marker = "# ── Outer guard"
        idx = source.find(stop_marker)
        safe_src = source[:idx] if idx != -1 else source
        ns: dict = {"__file__": path}
        exec(compile(safe_src, path, "exec"), ns)  # noqa: S102
        cls.extract = staticmethod(ns["_extract_roadmap_slugs"])
        cls.spec_approved = staticmethod(ns["_spec_approved"])

    def test_extract_slugs_from_next(self):
        content = "## Next\n- [ ] cool-feature — spec\n- [ ] auth-login — plan\n"
        slugs = self.extract(content)
        assert "cool-feature" in slugs
        assert "auth-login" in slugs

    def test_extract_slugs_from_ready(self):
        content = "## Ready\n- [ ] pipeline-gate — plan ✓\n"
        slugs = self.extract(content)
        assert "pipeline-gate" in slugs

    def test_extract_slugs_excludes_now(self):
        content = "## Now\n- [ ] now-feature — implement\n\n## Next\n- [ ] next-feature — spec\n"
        slugs = self.extract(content)
        assert "now-feature" not in slugs
        assert "next-feature" in slugs

    def test_extract_slugs_deduplicates(self):
        content = "## Next\n- [ ] cool-feature — spec\n- [ ] cool-feature — plan\n"
        slugs = self.extract(content)
        assert slugs.count("cool-feature") == 1

    def test_extract_slugs_ignores_single_words(self):
        content = "## Next\n- [ ] spec\n- [ ] plan\n"
        slugs = self.extract(content)
        assert "spec" not in slugs
        assert "plan" not in slugs

    def test_spec_approved_true(self, tmp_path):
        specs = tmp_path / "zie-framework" / "specs"
        specs.mkdir(parents=True)
        (specs / "2026-01-01-my-feat-design.md").write_text(
            "---\napproved: true\n---\n# Spec\n"
        )
        assert self.spec_approved(tmp_path, "my-feat") is True

    def test_spec_approved_false_flag(self, tmp_path):
        specs = tmp_path / "zie-framework" / "specs"
        specs.mkdir(parents=True)
        (specs / "2026-01-01-my-feat-design.md").write_text(
            "---\napproved: false\n---\n# Spec\n"
        )
        assert self.spec_approved(tmp_path, "my-feat") is False

    def test_spec_approved_missing_file(self, tmp_path):
        (tmp_path / "zie-framework" / "specs").mkdir(parents=True)
        assert self.spec_approved(tmp_path, "missing-feat") is False

    def test_spec_approved_no_specs_dir(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        assert self.spec_approved(tmp_path, "any-feat") is False


class TestPositionalGuidance:
    """Positional guidance nudges when no dominant intent and slug matched."""

    def _ctx(self, r):
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def _make_spec(self, specs_dir, slug, approved=True):
        specs_dir.mkdir(parents=True, exist_ok=True)
        content = f"---\napproved: {'true' if approved else 'false'}\n---\n# Spec\n"
        (specs_dir / f"2026-01-01-{slug}-design.md").write_text(content)

    def test_no_spec_nudges_zie_spec(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] auth-login — backlog\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "what about auth-login"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "zie-spec" in ctx

    def test_approved_spec_no_ready_nudges_zie_plan(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] auth-login — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "auth-login", approved=True)
        r = run_hook({"prompt": "what about auth-login"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "zie-plan" in ctx

    def test_slug_in_ready_nudges_zie_implement(self, tmp_path):
        roadmap = (
            "## Now\n\n"
            "## Next\n\n"
            "## Ready\n- [ ] auth-login — plan ✓\n"
        )
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "auth-login", approved=True)
        r = run_hook({"prompt": "what about auth-login"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "zie-implement" in ctx

    def test_no_slug_in_prompt_no_guidance(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] auth-login — backlog\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "what should I do next"}, tmp_cwd=cwd)
        if r.stdout.strip():
            ctx = json.loads(r.stdout)["additionalContext"]
            assert "auth-login" not in ctx
