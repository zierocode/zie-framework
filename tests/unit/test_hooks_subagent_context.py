"""Tests for hooks/subagent-context.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import write_roadmap_cache

SAMPLE_ROADMAP = """\
## Now

- [ ] [subagentstart-sdlc-context](plans/2026-03-24-subagentstart-sdlc-context.md)

## Next

- [ ] some-future-feature
"""

SAMPLE_PLAN = """\
# SubagentStart SDLC Context Injection — Implementation Plan

## Task 1: Create hooks/subagent-context.py

- [ ] **Step 1: Write failing tests (RED)**
- [ ] **Step 2: Implement (GREEN)**
- [ ] **Step 3: Refactor**
"""

SAMPLE_PLAN_ALL_DONE = """\
# SubagentStart SDLC Context Injection — Implementation Plan

## Task 1: Create hooks/subagent-context.py

- [x] **Step 1: Write failing tests (RED)**
- [x] **Step 2: Implement (GREEN)**
- [x] **Step 3: Refactor**
"""

SAMPLE_CONTEXT_MD = """\
## ADR-001

Some decision.

## ADR-002

Another decision.
"""


def make_cwd(tmp_path, roadmap=None, plan=None, context_md=None):
    """Build a minimal zie-framework directory structure for testing."""
    zf = tmp_path / "zie-framework"
    (zf / "plans").mkdir(parents=True)
    (zf / "project").mkdir(parents=True)

    if roadmap is not None:
        (zf / "ROADMAP.md").write_text(roadmap)

    if plan is not None:
        (zf / "plans" / "2026-03-24-subagentstart-sdlc-context.md").write_text(plan)

    if context_md is not None:
        (zf / "project" / "context.md").write_text(context_md)

    return tmp_path


def run_hook(event, tmp_cwd=None, env_overrides=None, session_id=None):
    hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    if session_id is None:
        session_id = f"test-sac-{abs(hash(str(tmp_cwd))) % 999999}"
    ev = {"session_id": session_id, **event}
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(ev),
        capture_output=True,
        text=True,
        env=env,
    )


def parse_context(r):
    """Assert stdout is non-empty JSON and return the additionalContext string."""
    assert r.stdout.strip() != "", f"Expected stdout, got empty. stderr={r.stderr}"
    return json.loads(r.stdout)["additionalContext"]


# ── Happy path ────────────────────────────────────────────────────────────────

class TestSubagentContextHappyPath:
    def test_explore_agent_receives_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "[zie-framework]" in ctx
        assert "Active:" in ctx
        assert "Task:" in ctx
        assert "ADRs:" in ctx

    def test_plan_agent_receives_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Plan"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active:" in ctx

    def test_feature_slug_derived_from_roadmap_now(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "subagentstart-sdlc-context" in ctx

    def test_first_incomplete_task_extracted(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Step 1: Write failing tests (RED)" in ctx

    def test_adr_count_correct(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "ADRs: 2" in ctx

    def test_all_tasks_complete_message(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN_ALL_DONE,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "all tasks complete" in ctx

    def test_returns_valid_json(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        parsed = json.loads(r.stdout)
        assert "additionalContext" in parsed
        assert isinstance(parsed["additionalContext"], str)

    def test_exit_code_zero_on_success(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        assert r.returncode == 0


# ── Agent-type filter ─────────────────────────────────────────────────────────

class TestSubagentContextAgentFilter:
    def test_task_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Task"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_build_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Build"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_coding_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Coding"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_empty_agent_type_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": ""}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_missing_agent_type_field_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_case_insensitive_explore_match(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active:" in ctx


# ── Edge cases: missing files ─────────────────────────────────────────────────

class TestSubagentContextMissingFiles:
    def test_no_roadmap_emits_active_none(self, tmp_path):
        cwd = make_cwd(tmp_path, plan=SAMPLE_PLAN, context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active: none" in ctx

    def test_no_plan_files_emits_task_unknown(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Task: unknown" in ctx

    def test_missing_context_md_emits_adr_unknown(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "ADRs: unknown" in ctx

    def test_no_roadmap_no_plan_still_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        assert r.returncode == 0

    def test_no_zf_dir_produces_no_output(self, tmp_path):
        r = run_hook({"agentType": "Explore"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0


# ── Guardrails ────────────────────────────────────────────────────────────────

class TestSubagentContextGuardrails:
    def test_invalid_json_stdin_exits_zero(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, hook],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_stdin_exits_zero(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, hook],
            input="",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0

    def test_no_stdout_for_non_matching_agent_even_with_full_files(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Task"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""
        assert r.returncode == 0


# ── hooks.json registration ───────────────────────────────────────────────────

class TestHooksJsonRegistration:
    def test_subagentstart_key_present(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        assert "SubagentStart" in data["hooks"], \
            "SubagentStart key missing from hooks.json"

    def test_subagentstart_matcher_is_explore_or_plan(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        entry = data["hooks"]["SubagentStart"]
        assert len(entry) > 0
        assert entry[0].get("matcher") == "Explore|Plan", \
            f"Expected matcher 'Explore|Plan', got {entry[0].get('matcher')!r}"

    def test_subagentstart_command_references_correct_script(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        entry = data["hooks"]["SubagentStart"]
        command = entry[0]["hooks"][0]["command"]
        assert "subagent-context.py" in command
        assert "${CLAUDE_PLUGIN_ROOT}" in command

    def test_existing_hooks_unchanged(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        hooks = data["hooks"]
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks, f"Existing hook key {key!r} was removed"


# ── components.md ─────────────────────────────────────────────────────────────

class TestComponentsRegistryUpdated:
    def test_subagent_context_in_components_md(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        text = components.read_text()
        assert "subagent-context.py" in text, \
            "subagent-context.py not found in components.md Hooks table"

    def test_subagentstart_event_listed(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        text = components.read_text()
        assert "SubagentStart" in text, \
            "SubagentStart event not listed in components.md"


class TestSubagentContextRoadmapCache:
    """Verify subagent-context uses ROADMAP cache when available."""

    def test_uses_cache_over_disk(self, tmp_path):
        """Cache content takes priority over disk ROADMAP."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        # Disk: empty Now
        (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n")
        sid = "test-subagent-cache-unique-88z"
        # Cache: active feature
        write_roadmap_cache(sid, "## Now\n- [ ] cached-subagent-feature\n\n## Next\n")
        event = {"agentType": "Explore", "session_id": sid}
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path), "ZIE_MEMORY_API_KEY": ""}
        hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
        r = subprocess.run(
            [sys.executable, hook], input=json.dumps(event),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        ctx = json.loads(r.stdout)["additionalContext"]
        # Should reflect cached task slug, not "none" from empty disk
        assert "cached" in ctx or "subagent" in ctx.lower()
