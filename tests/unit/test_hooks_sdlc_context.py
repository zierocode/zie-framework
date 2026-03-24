"""Tests for hooks/sdlc-context.py"""
import os
import sys
import json
import subprocess
import time
import pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "sdlc-context.py")
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import project_tmp_path

ROADMAP_WITH_IMPLEMENT = """\
## Now
- [ ] implement login flow — [plan](plans/login.md)

## Next
- [ ] Add refresh tokens
"""

ROADMAP_WITH_SPEC = """\
## Now
- [ ] write spec for payment module

## Next
- [ ] plan the implementation
"""

ROADMAP_WITH_FIX = """\
## Now
- [ ] fix bug in auth module

## Next
- [ ] deploy to staging
"""

ROADMAP_WITH_RELEASE = """\
## Now
- [ ] release v2.0

## Next
- [ ] retro
"""

ROADMAP_WITH_RETRO = """\
## Now
- [ ] retro — review the sprint

## Next
- [ ] backlog grooming
"""

ROADMAP_EMPTY_NOW = """\
## Now

## Next
- [ ] future task
"""

ROADMAP_LONG_TASK = """\
## Now
- [ ] """ + ("x" * 100) + """

## Next
- [ ] other
"""


def run_hook(event, tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap is not None:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


def parse_context(r):
    return json.loads(r.stdout)["additionalContext"]


class TestSdlcContextHappyPath:
    def test_emits_additionalcontext_json(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        parsed = json.loads(r.stdout)
        assert "additionalContext" in parsed

    def test_additionalcontext_contains_sdlc_prefix(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        assert parse_context(r).startswith("[sdlc]")

    def test_additionalcontext_has_all_four_fields(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "task:" in ctx
        assert "stage:" in ctx
        assert "next:" in ctx
        assert "tests:" in ctx

    def test_hook_specific_output_present(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        parsed = json.loads(r.stdout)
        assert parsed.get("hookSpecificOutput", {}).get("hookEventName") == "UserPromptSubmit"

    def test_active_task_from_now_lane(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "implement login flow" in ctx

    def test_active_task_truncated_to_80_chars(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_LONG_TASK)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        task_part = ctx.split("task:")[1].split("|")[0].strip()
        assert len(task_part) <= 80

    def test_no_updated_prompt_emitted(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        parsed = json.loads(r.stdout)
        assert "updatedPrompt" not in parsed


class TestSdlcContextStageDetection:
    def test_implement_stage_from_keyword(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: implement" in ctx

    def test_spec_stage_from_keyword(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_SPEC)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: spec" in ctx

    def test_fix_stage_from_keyword(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_FIX)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: fix" in ctx

    def test_release_stage_from_keyword(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_RELEASE)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: release" in ctx

    def test_retro_stage_from_keyword(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_RETRO)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: retro" in ctx

    def test_plan_stage_from_keyword(self, tmp_path):
        roadmap = "## Now\n- [ ] plan the next sprint\n"
        cwd = make_cwd(tmp_path, roadmap=roadmap)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: plan" in ctx

    def test_unrecognised_keyword_gives_in_progress(self, tmp_path):
        roadmap = "## Now\n- [ ] update the readme file\n"
        cwd = make_cwd(tmp_path, roadmap=roadmap)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: in-progress" in ctx

    def test_implement_stage_maps_to_zie_implement_cmd(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "next: /zie-implement" in ctx

    def test_spec_stage_maps_to_zie_spec_cmd(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_SPEC)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "next: /zie-spec" in ctx

    def test_fix_stage_maps_to_zie_fix_cmd(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_FIX)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "next: /zie-fix" in ctx


class TestSdlcContextEdgeCases:
    def test_empty_now_lane_active_task_none(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_EMPTY_NOW)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "task: none" in ctx

    def test_empty_now_lane_stage_idle(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_EMPTY_NOW)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "stage: idle" in ctx

    def test_empty_now_lane_next_is_zie_status(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_EMPTY_NOW)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "next: /zie-status" in ctx

    def test_missing_roadmap_file_idle(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=None)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "task: none" in ctx
        assert "stage: idle" in ctx

    def test_missing_roadmap_still_emits_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=None)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_no_output_when_zf_dir_absent(self, tmp_path):
        r = run_hook({"prompt": "hello"}, tmp_cwd=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_invalid_json_stdin_exits_zero_no_output(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not valid json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_long_prompt_does_not_affect_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "x" * 2000}, tmp_cwd=cwd)
        assert r.stdout.strip() != ""
        ctx = parse_context(r)
        assert "[sdlc]" in ctx

    def test_empty_prompt_still_emits_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": ""}, tmp_cwd=cwd)
        assert r.stdout.strip() != ""

    def test_concurrent_reads_exit_zero(self, tmp_path):
        """Multiple simultaneous hook runs must all exit 0 (read-only, no locks)."""
        import concurrent.futures
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)

        def invoke(_):
            return run_hook({"prompt": "hello"}, tmp_cwd=cwd)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(invoke, range(5)))

        for r in results:
            assert r.returncode == 0
            assert r.stdout.strip() != ""


class TestSdlcContextTestStatus:
    def test_tests_unknown_when_tmp_file_absent(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        tmp_file = project_tmp_path("last-test", tmp_path.name)
        if tmp_file.exists():
            tmp_file.unlink()
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "tests: unknown" in ctx

    def test_tests_recent_when_tmp_file_fresh(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        tmp_file = project_tmp_path("last-test", tmp_path.name)
        tmp_file.write_text("ok")
        try:
            r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
            ctx = parse_context(r)
            assert "tests: recent" in ctx
        finally:
            if tmp_file.exists():
                tmp_file.unlink()

    def test_tests_stale_when_tmp_file_old(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        tmp_file = project_tmp_path("last-test", tmp_path.name)
        tmp_file.write_text("ok")
        old_time = time.time() - 400
        os.utime(tmp_file, (old_time, old_time))
        try:
            r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
            ctx = parse_context(r)
            assert "tests: stale" in ctx
        finally:
            if tmp_file.exists():
                tmp_file.unlink()


class TestHooksJsonRegistration:
    def test_sdlc_context_registered_in_hooks_json(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        user_prompt_hooks = data["hooks"]["UserPromptSubmit"]
        all_commands = [
            h["command"]
            for group in user_prompt_hooks
            for h in group.get("hooks", [])
        ]
        assert any("sdlc-context.py" in cmd for cmd in all_commands), (
            "sdlc-context.py not found in UserPromptSubmit hooks"
        )

    def test_intent_detect_still_registered(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        user_prompt_hooks = data["hooks"]["UserPromptSubmit"]
        all_commands = [
            h["command"]
            for group in user_prompt_hooks
            for h in group.get("hooks", [])
        ]
        assert any("intent-detect.py" in cmd for cmd in all_commands), (
            "intent-detect.py was removed from UserPromptSubmit — it must remain"
        )

    def test_both_hooks_present_as_separate_commands(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        user_prompt_hooks = data["hooks"]["UserPromptSubmit"]
        all_commands = [
            h["command"]
            for group in user_prompt_hooks
            for h in group.get("hooks", [])
        ]
        sdlc_present = any("sdlc-context.py" in c for c in all_commands)
        intent_present = any("intent-detect.py" in c for c in all_commands)
        assert sdlc_present and intent_present, (
            f"Expected both hooks; found: {all_commands}"
        )


class TestSdlcContextNonInterference:
    def test_intent_detect_still_outputs_on_fix_prompt(self, tmp_path):
        """intent-detect.py must still suggest /zie-fix independently."""
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        intent_hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "CLAUDE_CWD": str(cwd)}
        r = subprocess.run(
            [sys.executable, intent_hook],
            input=json.dumps({"prompt": "fix this bug in auth"}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert "/zie-fix" in r.stdout

    def test_sdlc_context_output_does_not_contain_intent_detect_prefix(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "fix this bug"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert ctx.startswith("[sdlc]")
        assert "Detected:" not in ctx

    def test_no_output_from_sdlc_when_zf_absent_even_with_fix_prompt(self, tmp_path):
        r = run_hook({"prompt": "fix this bug"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""

    def test_sdlc_context_never_emits_updated_prompt(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
        r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
        parsed = json.loads(r.stdout)
        assert "updatedPrompt" not in parsed
