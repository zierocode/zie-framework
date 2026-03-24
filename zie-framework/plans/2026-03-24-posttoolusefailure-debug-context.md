---
approved: true
approved_at: 2026-03-24
backlog: backlog/posttoolusefailure-debug-context.md
spec: specs/2026-03-24-posttoolusefailure-debug-context-design.md
---

# PostToolUseFailure Debugging Context Injection — Implementation Plan

**Goal:** Create `hooks/failure-context.py` — a `PostToolUseFailure` hook that
injects SDLC context (active task, branch, last commit, quick-fix hint) into
Claude's view the moment a `Bash`, `Write`, or `Edit` tool call fails, reducing
diagnostic turns.

**Architecture:** Hook reads `PostToolUseFailure` event from stdin via
`read_event()`. Outer guard filters interrupts and out-of-scope tools. Inner
operation collects git context + ROADMAP Now lane, then prints
`{"additionalContext": "..."}` to stdout. Read-only — no tmp files, no race
conditions.

**Tech Stack:** Python 3.x, pytest, stdlib only (`json`, `subprocess`, `sys`,
`os`, `pathlib`)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/failure-context.py` | PostToolUseFailure hook — primary deliverable |
| Create | `tests/unit/test_hooks_failure_context.py` | Unit tests (7 cases from spec) |
| Modify | `hooks/hooks.json` | Register `PostToolUseFailure` event + update `_hook_output_protocol` |
| Modify | `zie-framework/project/components.md` | Add hook row to Hooks table |

---

## Task 1: Create `hooks/failure-context.py`

<!-- depends_on: none -->

**Acceptance Criteria:**

- On a normal `Bash`/`Write`/`Edit` failure: stdout is valid JSON with key
  `additionalContext` containing active task, branch, last commit, and
  `make test-unit` hint.
- On `is_interrupt: true`: stdout is empty, exit 0.
- On tool not in `{Bash, Write, Edit}`: stdout is empty, exit 0.
- On missing ROADMAP or empty Now lane: active task renders as
  `"(none — check ROADMAP Now lane)"`.
- On git unavailable or timeout: both git fields render as
  `"(git unavailable)"`.
- Hook never exits non-zero; never raises an unhandled exception.

**Files:**

- Create: `hooks/failure-context.py`
- Create: `tests/unit/test_hooks_failure_context.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_failure_context.py

  """Tests for hooks/failure-context.py — PostToolUseFailure debug context."""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  import pytest

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "failure-context.py")
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))

  SAMPLE_ROADMAP = """## Now\n- [ ] Implement failure-context hook\n"""
  ROADMAP_EMPTY_NOW = """## Now\n\n## Next\n- [ ] Some future task\n"""


  def run_hook(event: dict, tmp_cwd=None, env_overrides=None):
      env = {**os.environ}
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
      if roadmap:
          (zf / "ROADMAP.md").write_text(roadmap)
      return tmp_path


  # ── Test cases ────────────────────────────────────────────────────────────


  class TestNormalFailure:
      """TC-1: Normal failure with ROADMAP Now item present."""

      def test_additionalcontext_contains_task(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Bash"}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          data = json.loads(result.stdout)
          assert "additionalContext" in data
          assert "Implement failure-context hook" in data["additionalContext"]

      def test_additionalcontext_contains_branch(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Bash"}
          result = run_hook(event, tmp_cwd=cwd)
          data = json.loads(result.stdout)
          assert "Branch:" in data["additionalContext"]

      def test_additionalcontext_contains_last_commit(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Bash"}
          result = run_hook(event, tmp_cwd=cwd)
          data = json.loads(result.stdout)
          assert "Last commit:" in data["additionalContext"]

      def test_additionalcontext_contains_quick_fix_hint(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Edit"}
          result = run_hook(event, tmp_cwd=cwd)
          data = json.loads(result.stdout)
          assert "make test-unit" in data["additionalContext"]


  class TestInterrupt:
      """TC-2: is_interrupt: true — hook must emit nothing."""

      def test_empty_stdout_on_interrupt(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Bash", "is_interrupt": True}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          assert result.stdout == ""

      def test_exit_zero_on_interrupt(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {"tool_name": "Write", "is_interrupt": True}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0


  class TestMissingRoadmap:
      """TC-3: ROADMAP.md absent — active task fallback."""

      def test_fallback_task_when_roadmap_missing(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=None)
          event = {"tool_name": "Write"}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          data = json.loads(result.stdout)
          assert "(none — check ROADMAP Now lane)" in data["additionalContext"]


  class TestEmptyNowLane:
      """TC-4: ROADMAP Now lane has no items."""

      def test_fallback_task_when_now_lane_empty(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_EMPTY_NOW)
          event = {"tool_name": "Bash"}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          data = json.loads(result.stdout)
          assert "(none — check ROADMAP Now lane)" in data["additionalContext"]


  class TestToolFilter:
      """TC-5: Tool not in {Bash, Write, Edit} — emit nothing."""

      @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "ListFiles", ""])
      def test_empty_stdout_for_out_of_scope_tool(self, tmp_path, tool):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": tool}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          assert result.stdout == ""

      def test_missing_tool_name_key(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {}  # no tool_name key at all
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          assert result.stdout == ""


  class TestGitUnavailable:
      """TC-6: git unavailable — both git fields use fallback string."""

      def test_git_unavailable_fallback(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Bash"}
          # Override PATH to an empty dir so git cannot be found
          env_overrides = {"PATH": str(tmp_path)}
          result = run_hook(event, tmp_cwd=cwd, env_overrides=env_overrides)
          assert result.returncode == 0
          data = json.loads(result.stdout)
          ctx = data["additionalContext"]
          assert "(git unavailable)" in ctx


  class TestOutputProtocol:
      """TC-7: Output is valid JSON with additionalContext key."""

      @pytest.mark.parametrize("tool", ["Bash", "Write", "Edit"])
      def test_valid_json_output(self, tmp_path, tool):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": tool}
          result = run_hook(event, tmp_cwd=cwd)
          assert result.returncode == 0
          parsed = json.loads(result.stdout)
          assert isinstance(parsed, dict)
          assert "additionalContext" in parsed
          assert isinstance(parsed["additionalContext"], str)

      def test_output_is_single_json_object(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          event = {"tool_name": "Edit"}
          result = run_hook(event, tmp_cwd=cwd)
          # Must be exactly one JSON object — no trailing newlines that break parsing
          assert result.stdout.strip() != ""
          json.loads(result.stdout)  # raises if invalid
  ```

  Run: `make test-unit` — must **FAIL** (`failure-context.py` does not exist yet,
  all subprocess runs error out)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/failure-context.py

  #!/usr/bin/env python3
  """PostToolUseFailure hook — inject SDLC debug context on tool failure."""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import read_event, get_cwd, parse_roadmap_now

  ALLOWED_TOOLS = {"Bash", "Write", "Edit"}

  # ── Outer guard ──────────────────────────────────────────────────────────────

  try:
      event = read_event()
  except Exception:
      sys.exit(0)

  try:
      if event.get("is_interrupt", False):
          sys.exit(0)

      tool_name = event.get("tool_name", "")
      if tool_name not in ALLOWED_TOOLS:
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # ── Inner operations ─────────────────────────────────────────────────────────

  try:
      cwd = get_cwd()

      # ROADMAP Now lane
      roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
      try:
          now_items = parse_roadmap_now(roadmap_path)
      except Exception:
          now_items = []
      active_task = now_items[0] if now_items else "(none — check ROADMAP Now lane)"

      # Git last commit
      try:
          log_result = subprocess.run(
              ["git", "log", "-1", "--pretty=%h %s"],
              capture_output=True, text=True, cwd=str(cwd), timeout=5,
          )
          last_commit = log_result.stdout.strip() if log_result.returncode == 0 else "(git unavailable)"
      except Exception:
          last_commit = "(git unavailable)"

      # Git branch
      try:
          branch_result = subprocess.run(
              ["git", "rev-parse", "--abbrev-ref", "HEAD"],
              capture_output=True, text=True, cwd=str(cwd), timeout=5,
          )
          branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "(unknown)"
      except Exception:
          branch = "(unknown)"

      # Build context string
      context_string = (
          "[SDLC context at failure]\n"
          f"Active task: {active_task}\n"
          f"Branch: {branch}\n"
          f"Last commit: {last_commit}\n"
          "Quick fix: run `make test-unit` to reproduce; check output above for root cause."
      )

      print(json.dumps({"additionalContext": context_string}))

  except Exception as e:
      print(f"[zie-framework] failure-context: {e}", file=sys.stderr)

  sys.exit(0)
  ```

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  Review checklist before declaring GREEN stable:

  - Confirm the two-tier pattern is intact: outer guard uses bare `except
    Exception` → `sys.exit(0)`; inner operations use
    `except Exception as e: print(..., file=sys.stderr)`.
  - Confirm `sys.exit(0)` is always the final statement (never omitted by any
    early-return path).
  - Confirm `last_commit` and `branch` fallbacks are never left unset (both
    `except Exception` branches assign the fallback string before the git
    result is used).
  - Confirm `parse_roadmap_now` is called inside an inner try/except so a
    corrupted ROADMAP does not surface to the outer guard.
  - No structural changes to logic are needed; this step is
    confirmation-only.

  Run: `make test-unit` — still **PASS**

---

## Task 2: Register `PostToolUseFailure` in `hooks/hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `hooks.json` contains a top-level `PostToolUseFailure` key inside `"hooks"`.
- The matcher is exactly `"Bash|Write|Edit"`.
- The command path uses `${CLAUDE_PLUGIN_ROOT}` and points to `failure-context.py`.
- `_hook_output_protocol` is updated to document the `PostToolUseFailure`
  output format.
- All existing hook entries are unchanged.
- `make test-unit` continues to pass.

**Files:**

- Modify: `hooks/hooks.json`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_hooks_json.py  (create if not present, else add class)

  """Structural tests for hooks/hooks.json."""
  import json
  import os

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOKS_JSON = os.path.join(REPO_ROOT, "hooks", "hooks.json")


  class TestHooksJsonStructure:
      def _load(self):
          with open(HOOKS_JSON) as f:
              return json.load(f)

      def test_posttoolusefailure_key_exists(self):
          data = self._load()
          assert "PostToolUseFailure" in data["hooks"], (
              "PostToolUseFailure entry missing from hooks.json"
          )

      def test_posttoolusefailure_matcher(self):
          data = self._load()
          entry = data["hooks"]["PostToolUseFailure"][0]
          assert entry["matcher"] == "Bash|Write|Edit"

      def test_posttoolusefailure_command_path(self):
          data = self._load()
          entry = data["hooks"]["PostToolUseFailure"][0]
          cmd = entry["hooks"][0]["command"]
          assert "failure-context.py" in cmd
          assert "${CLAUDE_PLUGIN_ROOT}" in cmd

      def test_hook_output_protocol_documents_posttoolusefailure(self):
          data = self._load()
          protocol = data.get("_hook_output_protocol", {})
          assert "PostToolUseFailure" in protocol, (
              "_hook_output_protocol must document PostToolUseFailure"
          )

      def test_existing_hooks_unchanged(self):
          data = self._load()
          hooks = data["hooks"]
          # Existing top-level keys must still be present
          for key in ["SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"]:
              assert key in hooks, f"Existing hook key '{key}' was removed"
  ```

  Run: `make test-unit` — must **FAIL** (`PostToolUseFailure` absent,
  `_hook_output_protocol` not updated)

---

- [ ] **Step 2: Implement (GREEN)**

  Edit `hooks/hooks.json` — two changes:

  **Change 1** — add `PostToolUseFailure` to `_hook_output_protocol`:

  ```json
  "_hook_output_protocol": {
    "SessionStart": "plain text printed to stdout — injected as session context",
    "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
    "PostToolUse": "plain text warnings/status printed to stdout",
    "PostToolUseFailure": "JSON {\"additionalContext\": \"...\"} printed to stdout",
    "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
    "Stop": "no output required; side-effects only (file writes, API calls)"
  }
  ```

  **Change 2** — add `PostToolUseFailure` block inside `"hooks"` (after the
  `PreToolUse` block, before `Stop`):

  ```json
  "PostToolUseFailure": [
    {
      "matcher": "Bash|Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/failure-context.py\""
        }
      ]
    }
  ]
  ```

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  - Confirm JSON is valid (parse with `python3 -c "import json; json.load(open('hooks/hooks.json'))"`).
  - Confirm key ordering in `_hook_output_protocol` follows event lifecycle:
    SessionStart → UserPromptSubmit → PreToolUse → PostToolUse →
    PostToolUseFailure → Stop.
  - No logic changes needed.

  Run: `make test-unit` — still **PASS**

---

## Task 3: Update `zie-framework/project/components.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- Hooks table contains a row for `failure-context.py`.
- Row describes the event (`PostToolUseFailure:Bash/Write/Edit`) and what the
  hook does.
- `Last updated` date is updated to `2026-03-24`.
- No other rows are modified.

**Files:**

- Modify: `zie-framework/project/components.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_components_registry.py  (create if not present, else add class)

  """Smoke-test the components registry stays current."""
  import os

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  COMPONENTS = os.path.join(
      REPO_ROOT, "zie-framework", "project", "components.md"
  )


  class TestComponentsRegistry:
      def _content(self):
          with open(COMPONENTS) as f:
              return f.read()

      def test_failure_context_hook_present(self):
          assert "failure-context.py" in self._content(), (
              "failure-context.py missing from components.md Hooks table"
          )

      def test_posttoolusefailure_event_documented(self):
          assert "PostToolUseFailure" in self._content()
  ```

  Run: `make test-unit` — must **FAIL** (`failure-context.py` absent from
  components.md)

---

- [ ] **Step 2: Implement (GREEN)**

  In `zie-framework/project/components.md`, append a new row to the Hooks
  table and update `Last updated`:

  ```markdown
  | failure-context.py | PostToolUseFailure:Bash/Write/Edit | inject SDLC debug context (active task, branch, last commit, quick-fix hint); is_interrupt guard |
  ```

  Also update the header line:

  ```markdown
  **Last updated:** 2026-03-24
  ```

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  Confirm the new row aligns with the existing column order
  (Hook | Event | ทำอะไร). No logic changes needed.

  Run: `make test-unit` — still **PASS**

---

## Commit

```
git add hooks/failure-context.py \
        hooks/hooks.json \
        tests/unit/test_hooks_failure_context.py \
        tests/unit/test_hooks_json.py \
        tests/unit/test_components_registry.py \
        zie-framework/project/components.md \
  && git commit -m "feat: PostToolUseFailure hook injects SDLC debug context on tool failure"
```
