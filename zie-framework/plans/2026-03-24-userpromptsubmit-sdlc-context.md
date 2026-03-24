---
approved: true
approved_at: 2026-03-24
backlog: backlog/userpromptsubmit-sdlc-context.md
spec: specs/2026-03-24-userpromptsubmit-sdlc-context-design.md
---

# UserPromptSubmit SDLC Context Injection — Implementation Plan

**Goal:** Add `hooks/sdlc-context.py`, a UserPromptSubmit hook that injects the active SDLC task, stage, suggested next command, and test freshness into every prompt's `additionalContext` so Claude is always stage-aware without extra turns.
**Architecture:** A new standalone hook reads `zie-framework/ROADMAP.md` via the existing `parse_roadmap_now` utility and checks the last-test tmp file mtime via `project_tmp_path` — no subprocess calls, pure file I/O, guaranteed sub-100ms. It is registered as a second entry in the `UserPromptSubmit` hooks array in `hooks.json` so it runs alongside `intent-detect.py` without touching that hook. The two hooks compose independently: `sdlc-context.py` always emits state context; `intent-detect.py` continues to pattern-match the prompt and suggest commands.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/sdlc-context.py` | UserPromptSubmit hook — reads ROADMAP Now lane + last-test mtime, emits `additionalContext` |
| Modify | `hooks/hooks.json` | Add second `UserPromptSubmit` entry for `sdlc-context.py` |
| Create | `tests/unit/test_hooks_sdlc_context.py` | Full pytest coverage for the new hook |

---

## Task 1: Create `hooks/sdlc-context.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Hook prints `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}, "additionalContext": "[sdlc] task: <task> | stage: <stage> | next: <cmd> | tests: <status>"}` to stdout on any prompt when `zie-framework/` is present in cwd
- `active_task` is truncated to 80 chars
- Stage is derived from keyword matching against the Now-lane item text (see keyword map below)
- `tests` field is `recent`, `stale`, or `unknown` based on last-test tmp mtime (stale threshold: 300 s)
- When `zie-framework/` is absent, hook exits 0 with no output
- On any inner exception (file I/O, mtime read), logs to stderr and exits 0 — Claude is never blocked
- Hook never emits `updatedPrompt`
- Hook does not read or use the prompt text at all

**Files:**
- Create: `hooks/sdlc-context.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_sdlc_context.py
  """Tests for hooks/sdlc-context.py"""
  import os, sys, json, subprocess, time, pytest
  from pathlib import Path
  from unittest.mock import patch

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "sdlc-context.py")

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
          # Markdown link stripped by parse_roadmap_now; task text included
          assert "implement login flow" in ctx

      def test_active_task_truncated_to_80_chars(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_LONG_TASK)
          r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
          ctx = parse_context(r)
          # Extract the task value from "task: <value> |"
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
          # zie-framework/ dir present but no ROADMAP.md
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
          # tmp_path has no zie-framework/ subdirectory
          r = run_hook({"prompt": "hello"}, tmp_cwd=tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_invalid_json_stdin_exits_zero_no_output(self, tmp_path):
          hook_path = os.path.join(REPO_ROOT, "hooks", "sdlc-context.py")
          env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
          r = subprocess.run(
              [sys.executable, hook_path],
              input="not valid json",
              capture_output=True,
              text=True,
              env=env,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_long_prompt_does_not_affect_output(self, tmp_path):
          # Hook ignores prompt content; long prompt must not suppress context
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
          # Ensure no stale tmp file exists for this project name
          tmp_file = Path(f"/tmp/zie-{tmp_path.name}-last-test")
          if tmp_file.exists():
              tmp_file.unlink()
          r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
          ctx = parse_context(r)
          assert "tests: unknown" in ctx

      def test_tests_recent_when_tmp_file_fresh(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
          tmp_file = Path(f"/tmp/zie-{tmp_path.name}-last-test")
          tmp_file.write_text("ok")
          # mtime is now — well within 300s threshold
          try:
              r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
              ctx = parse_context(r)
              assert "tests: recent" in ctx
          finally:
              if tmp_file.exists():
                  tmp_file.unlink()

      def test_tests_stale_when_tmp_file_old(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
          tmp_file = Path(f"/tmp/zie-{tmp_path.name}-last-test")
          tmp_file.write_text("ok")
          # Back-date mtime by 400 seconds
          old_time = time.time() - 400
          os.utime(tmp_file, (old_time, old_time))
          try:
              r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
              ctx = parse_context(r)
              assert "tests: stale" in ctx
          finally:
              if tmp_file.exists():
                  tmp_file.unlink()
  ```
  Run: `make test-unit` — must FAIL (module `sdlc-context` does not exist)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/sdlc-context.py
  #!/usr/bin/env python3
  """UserPromptSubmit hook — inject current SDLC state as additionalContext."""
  import json
  import os
  import sys
  import time
  from pathlib import Path

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import parse_roadmap_now, project_tmp_path, read_event, get_cwd

  # ── Stage keyword map (checked in order; first match wins) ──────────────────

  STAGE_KEYWORDS = [
      ("spec",      ["spec"]),
      ("plan",      ["plan"]),
      ("implement", ["implement", "code", "build"]),
      ("fix",       ["fix", "bug"]),
      ("release",   ["release", "deploy"]),
      ("retro",     ["retro"]),
  ]

  # ── Stage → suggested /zie-* command ────────────────────────────────────────

  STAGE_COMMANDS = {
      "spec":        "/zie-spec",
      "plan":        "/zie-plan",
      "implement":   "/zie-implement",
      "fix":         "/zie-fix",
      "release":     "/zie-release",
      "retro":       "/zie-retro",
      "in-progress": "/zie-status",
      "idle":        "/zie-status",
  }

  STALE_THRESHOLD_SECS = 300

  # ── Helpers ──────────────────────────────────────────────────────────────────

  def derive_stage(task_text: str) -> str:
      """Return SDLC stage name by matching task_text against STAGE_KEYWORDS."""
      lower = task_text.lower()
      for stage, keywords in STAGE_KEYWORDS:
          if any(kw in lower for kw in keywords):
              return stage
      return "in-progress"


  def get_test_status(cwd: Path) -> str:
      """Return 'recent', 'stale', or 'unknown' based on last-test tmp file mtime."""
      tmp_file = project_tmp_path("last-test", cwd.name)
      try:
          mtime = tmp_file.stat().st_mtime
          age = time.time() - mtime
          return "stale" if age > STALE_THRESHOLD_SECS else "recent"
      except Exception:
          return "unknown"

  # ── Hook execution ───────────────────────────────────────────────────────────

  # Outer guard — parse stdin; any failure exits 0 silently (read_event does this)
  try:
      event = read_event()
  except SystemExit:
      sys.exit(0)

  try:
      cwd = get_cwd()

      # Only run when zie-framework is initialized in this project
      if not (cwd / "zie-framework").exists():
          sys.exit(0)

      roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
      now_items = parse_roadmap_now(roadmap_path)

      if now_items:
          raw_task = now_items[0]
          active_task = raw_task[:80]
          stage = derive_stage(active_task)
      else:
          active_task = "none"
          stage = "idle"

      suggested_cmd = STAGE_COMMANDS.get(stage, "/zie-status")
      test_status = get_test_status(cwd)

      context = (
          f"[sdlc] task: {active_task} | "
          f"stage: {stage} | "
          f"next: {suggested_cmd} | "
          f"tests: {test_status}"
      )

      print(json.dumps({
          "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"},
          "additionalContext": context,
      }))

  except Exception as e:
      print(f"[zie-framework] sdlc-context: {e}", file=sys.stderr)
      sys.exit(0)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm `STAGE_KEYWORDS` and `STAGE_COMMANDS` are defined at module level (not inside the try block) so they are compiled once and not re-built per invocation.
  - Confirm `derive_stage` and `get_test_status` are pure functions with no side effects.
  - Confirm there is no `updatedPrompt` key anywhere in the output.
  - Confirm the outer guard uses bare `except Exception` pattern matching CLAUDE.md convention.
  Run: `make test-unit` — still PASS

---

## Task 2: Register hook in `hooks/hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks.json` has a second object inside the `UserPromptSubmit` hooks array with `sdlc-context.py`
- The existing `intent-detect.py` entry is unchanged
- Both hooks can run on the same event without interfering

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_sdlc_context.py — add new class at the end of the file

  class TestHooksJsonRegistration:
      def test_sdlc_context_registered_in_hooks_json(self):
          hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
          data = json.loads(hooks_json.read_text())
          user_prompt_hooks = data["hooks"]["UserPromptSubmit"]
          # Flatten all hook entries across all matchers/groups
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
  ```
  Run: `make test-unit` — must FAIL (`sdlc-context.py` not yet in `hooks.json`)

- [ ] **Step 2: Implement (GREEN)**
  Add `sdlc-context.py` as a second entry in the `UserPromptSubmit` array. The array currently has one object with one `hooks` entry. Add a second sibling object:

  ```json
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-detect.py\""
        }
      ]
    },
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/sdlc-context.py\""
        }
      ]
    }
  ]
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify `hooks.json` is valid JSON (`python3 -c "import json; json.load(open('hooks/hooks.json'))"`)
  - Verify no matcher key was added (hook fires on all prompts, by design)
  - Verify no other hook entries were disturbed
  Run: `make test-unit` — still PASS

---

## Task 3: Integration — verify no interference with `intent-detect.py`

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- `intent-detect.py` output is unaffected by `sdlc-context.py` running on the same event
- When prompt matches a known pattern, `intent-detect.py` still emits its own `additionalContext`
- When `zie-framework/` is absent, both hooks exit 0 with no output
- `sdlc-context.py` never outputs `updatedPrompt`

**Files:**
- Modify: `tests/unit/test_hooks_sdlc_context.py` (add class below)

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_sdlc_context.py — add at end of file

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
          # sdlc-context output must use [sdlc] prefix, not [zie-framework] intent prefix
          assert ctx.startswith("[sdlc]")
          assert "Detected:" not in ctx

      def test_no_output_from_sdlc_when_zf_absent_even_with_fix_prompt(self, tmp_path):
          # No zie-framework/ dir — both hooks must produce no output
          r = run_hook({"prompt": "fix this bug"}, tmp_cwd=tmp_path)
          assert r.stdout.strip() == ""

      def test_sdlc_context_never_emits_updated_prompt(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
          r = run_hook({"prompt": "hello"}, tmp_cwd=cwd)
          parsed = json.loads(r.stdout)
          assert "updatedPrompt" not in parsed
  ```
  Run: `make test-unit` — must FAIL (class references hook not yet implemented — covered by Task 1 being prerequisite; if Task 1 is complete, these tests should PASS immediately, confirming non-interference by construction)

- [ ] **Step 2: Implement (GREEN)**
  No new code — this task validates composition. If Task 1 and Task 2 are complete, all tests in `TestSdlcContextNonInterference` pass without changes.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review `sdlc-context.py` to confirm:
  - No import of `intent-detect` module
  - No shared mutable state with `intent-detect.py`
  - Both hooks output independent JSON objects; Claude Code aggregates them
  Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/sdlc-context.py hooks/hooks.json tests/unit/test_hooks_sdlc_context.py && git commit -m "feat: userpromptsubmit-sdlc-context"`*
