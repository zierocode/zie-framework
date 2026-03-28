---
approved: true
approved_at: 2026-03-24
backlog: backlog/subagent-lifecycle-hooks.md
spec: specs/2026-03-24-subagent-lifecycle-hooks-design.md
---

# SubagentStop Capture + Resume Subagent Pattern — Implementation Plan

**Goal:** Add a `SubagentStop` hook that appends a JSONL entry per completed subagent to a project-scoped `/tmp` log. Update `/zie-retro` to surface a "Subagent Activity" summary from the log. Document the resume pattern in `/zie-implement`.
**Architecture:** New `hooks/subagent-stop.py` registered as `async: true` in `hooks/hooks.json`. Uses existing `project_tmp_path`, `get_cwd`, and `read_event` from `utils.py` — no changes to utils required. JSONL append (not atomic rename) because this is a cumulative log with a single writer. Symlink guard mirrors `safe_write_tmp` pattern.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/subagent-stop.py` | SubagentStop event → JSONL append to `/tmp` log |
| Modify | `hooks/hooks.json` | Register `SubagentStop` entry with `async: true` |
| Create | `tests/unit/test_hooks_subagent_stop.py` | Full test suite for the new hook |
| Modify | `commands/zie-retro.md` | Add "Subagent Activity" section |
| Modify | `commands/zie-implement.md` | Add resume-subagent documentation block |

---

## JSONL Record Format

Each line written to `/tmp/zie-<safe_project>-subagent-log` is a self-contained JSON object followed by `\n`:

```json
{"ts": "2026-03-24T10:05:32.123456Z", "agent_id": "abc-123", "agent_type": "spec-reviewer", "last_message": "The spec looks good. One concern: ..."}
```

Field rules:
- `ts` — `datetime.utcnow().isoformat() + "Z"` (UTC, no timezone offset string)
- `agent_id` — `event.get("agent_id", "unknown")`
- `agent_type` — `event.get("agent_type", "unknown")`
- `last_message` — `str(event.get("last_assistant_message") or "")[:500]`

Log path: `project_tmp_path("subagent-log", cwd.name)` → `/tmp/zie-<safe_project>-subagent-log`

---

## Task 1: Create `hooks/subagent-stop.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Valid event with all fields → JSONL line appended to correct path, all fields match spec, `last_message` capped at 500 chars
- Missing fields → line written with `"unknown"` placeholders, no exception raised
- `last_assistant_message` is `None` → coerced to `""`, written cleanly
- Message of 1000 chars → stored as exactly 500 chars
- Non-zie project (no `zie-framework/` subdir) → nothing written, exits 0
- Symlink at log path → write skipped, warning on stderr, exits 0
- Malformed stdin → `read_event()` returns `{}` → outer guard `sys.exit(0)`, no crash
- Three events in sequence → three JSONL lines in order, each parseable
- Hook always exits 0; never raises

**Files:**
- Create: `hooks/subagent-stop.py`
- Create: `tests/unit/test_hooks_subagent_stop.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_subagent_stop.py

  """Tests for hooks/subagent-stop.py"""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  import pytest

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "subagent-stop.py")
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
  from utils import project_tmp_path


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


  def make_cwd(tmp_path):
      """Return tmp_path with a zie-framework/ subdir present."""
      (tmp_path / "zie-framework").mkdir(parents=True)
      return tmp_path


  VALID_EVENT = {
      "agent_id": "abc-123",
      "agent_type": "spec-reviewer",
      "last_assistant_message": "Looks good overall.",
  }


  # ---------------------------------------------------------------------------
  # Helpers / fixtures
  # ---------------------------------------------------------------------------

  @pytest.fixture(autouse=True)
  def _cleanup_log(tmp_path):
      yield
      log = project_tmp_path("subagent-log", tmp_path.name)
      if log.exists() or log.is_symlink():
          log.unlink(missing_ok=True)


  # ---------------------------------------------------------------------------
  # TestSubagentStopNormalWrite
  # ---------------------------------------------------------------------------

  class TestSubagentStopNormalWrite:
      def test_log_file_created_on_valid_event(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          assert log.exists(), f"log file not created at {log}"

      def test_log_contains_one_jsonl_line(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          lines = [l for l in log.read_text().splitlines() if l.strip()]
          assert len(lines) == 1

      def test_log_line_is_valid_json(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          line = log.read_text().strip()
          record = json.loads(line)  # must not raise
          assert isinstance(record, dict)

      def test_agent_id_field(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["agent_id"] == "abc-123"

      def test_agent_type_field(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["agent_type"] == "spec-reviewer"

      def test_last_message_field(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["last_message"] == "Looks good overall."

      def test_ts_field_present_and_ends_with_z(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook(VALID_EVENT, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert "ts" in record
          assert record["ts"].endswith("Z"), f"ts must end with Z, got: {record['ts']}"

      def test_exits_zero_on_valid_event(self, tmp_path):
          cwd = make_cwd(tmp_path)
          r = run_hook(VALID_EVENT, tmp_cwd=cwd)
          assert r.returncode == 0


  # ---------------------------------------------------------------------------
  # TestSubagentStopTruncation
  # ---------------------------------------------------------------------------

  class TestSubagentStopTruncation:
      def test_long_message_truncated_to_500(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {**VALID_EVENT, "last_assistant_message": "x" * 1000}
          run_hook(event, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert len(record["last_message"]) == 500

      def test_short_message_not_padded(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {**VALID_EVENT, "last_assistant_message": "short"}
          run_hook(event, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["last_message"] == "short"

      def test_exactly_500_message_unchanged(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {**VALID_EVENT, "last_assistant_message": "y" * 500}
          run_hook(event, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert len(record["last_message"]) == 500


  # ---------------------------------------------------------------------------
  # TestSubagentStopMissingFields
  # ---------------------------------------------------------------------------

  class TestSubagentStopMissingFields:
      def test_empty_event_writes_unknown_placeholders(self, tmp_path):
          cwd = make_cwd(tmp_path)
          run_hook({}, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          assert log.exists(), "log must be written even for empty event"
          record = json.loads(log.read_text().strip())
          assert record["agent_id"] == "unknown"
          assert record["agent_type"] == "unknown"
          assert record["last_message"] == ""

      def test_none_last_message_coerced_to_empty_string(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {"agent_id": "x", "agent_type": "y", "last_assistant_message": None}
          run_hook(event, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["last_message"] == ""

      def test_missing_agent_id_defaults_to_unknown(self, tmp_path):
          cwd = make_cwd(tmp_path)
          event = {"agent_type": "plan-reviewer", "last_assistant_message": "ok"}
          run_hook(event, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          record = json.loads(log.read_text().strip())
          assert record["agent_id"] == "unknown"

      def test_exits_zero_on_empty_event(self, tmp_path):
          cwd = make_cwd(tmp_path)
          r = run_hook({}, tmp_cwd=cwd)
          assert r.returncode == 0


  # ---------------------------------------------------------------------------
  # TestSubagentStopGuardrails
  # ---------------------------------------------------------------------------

  class TestSubagentStopGuardrails:
      def test_no_write_when_no_zf_dir(self, tmp_path):
          # tmp_path has no zie-framework/ subdir
          r = run_hook(VALID_EVENT, tmp_cwd=tmp_path)
          assert r.returncode == 0
          log = project_tmp_path("subagent-log", tmp_path.name)
          assert not log.exists(), "log must NOT be written on non-zie projects"

      def test_malformed_stdin_exits_zero(self):
          r = subprocess.run(
              [sys.executable, HOOK],
              input="not valid json }{",
              capture_output=True,
              text=True,
          )
          assert r.returncode == 0

      def test_empty_stdin_exits_zero(self):
          r = subprocess.run(
              [sys.executable, HOOK],
              input="",
              capture_output=True,
              text=True,
          )
          assert r.returncode == 0


  # ---------------------------------------------------------------------------
  # TestSubagentStopSymlinkGuard
  # ---------------------------------------------------------------------------

  class TestSubagentStopSymlinkGuard:
      def test_symlink_at_log_path_skips_write(self, tmp_path):
          cwd = make_cwd(tmp_path)
          real_target = tmp_path / "sensitive.txt"
          real_target.write_text("do not overwrite")
          log = project_tmp_path("subagent-log", tmp_path.name)
          log.symlink_to(real_target)

          r = run_hook(VALID_EVENT, tmp_cwd=cwd)

          assert r.returncode == 0
          assert real_target.read_text() == "do not overwrite", (
              "symlink target must not be overwritten"
          )

      def test_symlink_guard_prints_warning_to_stderr(self, tmp_path):
          cwd = make_cwd(tmp_path)
          real_target = tmp_path / "sensitive.txt"
          real_target.write_text("safe")
          log = project_tmp_path("subagent-log", tmp_path.name)
          log.symlink_to(real_target)

          r = run_hook(VALID_EVENT, tmp_cwd=cwd)

          assert "subagent" in r.stderr.lower() or "symlink" in r.stderr.lower(), (
              f"expected symlink warning on stderr, got: {r.stderr!r}"
          )


  # ---------------------------------------------------------------------------
  # TestSubagentStopMultipleEvents
  # ---------------------------------------------------------------------------

  class TestSubagentStopMultipleEvents:
      def test_three_events_produce_three_lines(self, tmp_path):
          cwd = make_cwd(tmp_path)
          events = [
              {"agent_id": "a1", "agent_type": "spec-reviewer", "last_assistant_message": "msg1"},
              {"agent_id": "a2", "agent_type": "plan-reviewer", "last_assistant_message": "msg2"},
              {"agent_id": "a3", "agent_type": "impl-reviewer", "last_assistant_message": "msg3"},
          ]
          for ev in events:
              run_hook(ev, tmp_cwd=cwd)
          log = project_tmp_path("subagent-log", tmp_path.name)
          lines = [l for l in log.read_text().splitlines() if l.strip()]
          assert len(lines) == 3

      def test_multiple_events_each_line_parseable(self, tmp_path):
          cwd = make_cwd(tmp_path)
          for i in range(3):
              run_hook(
                  {"agent_id": f"id-{i}", "agent_type": "reviewer", "last_assistant_message": f"msg{i}"},
                  tmp_cwd=cwd,
              )
          log = project_tmp_path("subagent-log", tmp_path.name)
          records = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
          assert [r["agent_id"] for r in records] == ["id-0", "id-1", "id-2"]

      def test_multiple_events_order_preserved(self, tmp_path):
          cwd = make_cwd(tmp_path)
          types = ["spec-reviewer", "plan-reviewer", "impl-reviewer"]
          for t in types:
              run_hook(
                  {"agent_id": "x", "agent_type": t, "last_assistant_message": ""},
                  tmp_cwd=cwd,
              )
          log = project_tmp_path("subagent-log", tmp_path.name)
          records = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
          assert [r["agent_type"] for r in records] == types
  ```

  Run: `make test-unit` — must FAIL (`hooks/subagent-stop.py` does not exist)

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/subagent-stop.py

  """SubagentStop hook — append completed subagent metadata to a JSONL log.

  Registered as async: true. Never blocks Claude.
  Two-tier error handling per zie-framework hook convention:
    Tier 1 (outer guard): parse + project check — bare except → sys.exit(0)
    Tier 2 (inner ops):   file I/O — except Exception as e → stderr + exit(0)
  """
  import json
  import os
  import sys
  from datetime import datetime
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent))
  from utils import get_cwd, project_tmp_path, read_event

  # --- Tier 1: outer guard ---------------------------------------------------
  try:
      event = read_event()
      cwd = get_cwd()
      if not (cwd / "zie-framework").is_dir():
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # --- Tier 2: inner operations ---------------------------------------------
  try:
      agent_id = event.get("agent_id", "unknown")
      agent_type = event.get("agent_type", "unknown")
      raw_msg = event.get("last_assistant_message")
      last_message = str(raw_msg or "")[:500]

      record = {
          "ts": datetime.utcnow().isoformat() + "Z",
          "agent_id": agent_id,
          "agent_type": agent_type,
          "last_message": last_message,
      }

      log_path = project_tmp_path("subagent-log", cwd.name)

      if os.path.islink(log_path):
          print(
              f"[zie-framework] subagent-stop: log path is a symlink, skipping write: {log_path}",
              file=sys.stderr,
          )
          sys.exit(0)

      with open(log_path, "a") as fh:
          fh.write(json.dumps(record) + "\n")

  except Exception as e:
      print(f"[zie-framework] subagent-stop: {e}", file=sys.stderr)

  sys.exit(0)
  ```

  Run: `make test-unit` — must PASS (all `TestSubagentStop*` classes green)

- [ ] **Step 3: Refactor**

  Review and confirm:
  - Docstring accurately describes both tiers.
  - No bare key access on `event` — all via `.get()` with defaults.
  - `sys.path.insert` uses `Path(__file__).parent` consistently with other hooks.
  - `sys.exit(0)` is the only exit path (check: no `exit()` or `raise` at module level).

  Run: `make test-unit` — still PASS

---

## Task 2: Register `SubagentStop` in `hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks.json` contains a `"SubagentStop"` top-level key inside `"hooks"`.
- The entry has `"async": true`.
- The command references `"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-stop.py"`.
- All existing hook entries remain unchanged.
- `hooks.json` is valid JSON (no trailing commas, correct structure).

**Files:**
- Modify: `hooks/hooks.json`
- No new test file needed — registration is verified by loading the JSON.

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_hooks_json.py — add new class (create file if absent)

  """Structural tests for hooks/hooks.json."""
  import json
  import os
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOKS_JSON = Path(REPO_ROOT) / "hooks" / "hooks.json"


  class TestHooksJsonSubagentStop:
      def _load(self):
          return json.loads(HOOKS_JSON.read_text())

      def test_hooks_json_is_valid_json(self):
          self._load()  # must not raise

      def test_subagent_stop_key_present(self):
          data = self._load()
          assert "SubagentStop" in data["hooks"], (
              "hooks.json must contain a SubagentStop entry"
          )

      def test_subagent_stop_has_async_true(self):
          data = self._load()
          entries = data["hooks"]["SubagentStop"]
          assert len(entries) == 1
          hook = entries[0]["hooks"][0]
          assert hook.get("async") is True, (
              "SubagentStop hook must have async: true"
          )

      def test_subagent_stop_command_references_correct_script(self):
          data = self._load()
          hook = data["hooks"]["SubagentStop"][0]["hooks"][0]
          assert "subagent-stop.py" in hook["command"]
          assert "${CLAUDE_PLUGIN_ROOT}" in hook["command"]

      def test_existing_hooks_unchanged(self):
          data = self._load()
          hooks = data["hooks"]
          for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
              assert key in hooks, f"existing hook key missing: {key}"
  ```

  Run: `make test-unit` — must FAIL (`SubagentStop` key absent)

- [ ] **Step 2: Implement (GREEN)**

  Add the `SubagentStop` entry to `hooks/hooks.json` after the `Stop` block, before the closing `}` of the `"hooks"` object:

  ```json
  "SubagentStop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-stop.py\"",
          "async": true
        }
      ]
    }
  ]
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm final `hooks.json` structure is consistent: all existing entries have the same `[{ "hooks": [{ "type": "command", "command": "..." }] }]` shape. Validate with `python3 -c "import json; json.load(open('hooks/hooks.json'))"`.

  Run: `make test-unit` — still PASS

---

## Task 3: Add "Subagent Activity" section to `/zie-retro`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `/zie-retro` reads `project_tmp_path("subagent-log", project)` at retro time.
- If the file exists: prints a summary table grouped by `agent_type` (columns: Type, Count, Last Agent ID snippet, Last Message snippet).
- If the file does not exist: prints "No subagent activity recorded this session." and continues without error.
- The new section appears under "รวบรวม context" before the analysis step.
- Existing retro flow and steps are unmodified.

**Files:**
- Modify: `commands/zie-retro.md`
- Create: `tests/unit/test_commands_retro_subagent.py`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_commands_retro_subagent.py

  """Structural tests: /zie-retro must reference the subagent-log."""
  import os
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  RETRO_CMD = Path(REPO_ROOT) / "commands" / "zie-retro.md"


  class TestRetroSubagentSection:
      def _src(self):
          return RETRO_CMD.read_text()

      def test_retro_references_subagent_log(self):
          assert "subagent-log" in self._src(), (
              "zie-retro.md must reference 'subagent-log' to read the JSONL log"
          )

      def test_retro_has_subagent_activity_heading(self):
          src = self._src()
          assert "Subagent Activity" in src, (
              "zie-retro.md must contain a 'Subagent Activity' section heading"
          )

      def test_retro_handles_missing_log_gracefully(self):
          src = self._src()
          assert "No subagent activity" in src, (
              "zie-retro.md must document the 'No subagent activity' fallback message"
          )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-retro.md`, add the following block inside "รวบรวม context", after step 1 (memory recall) and before the ADR count step:

  ```markdown
  2. **Subagent Activity** — read subagent log for this session:

     - Resolve log path: `project_tmp_path("subagent-log", project)` →
       `/tmp/zie-<project>-subagent-log`
     - If file exists: read line-by-line, parse each JSON record, group by
       `agent_type`. Print summary:

       ```text
       Subagent Activity This Session
       ───────────────────────────────────────────────────────
       Type              Count   Last Agent ID   Last Message
       spec-reviewer     2       abc-123         "The spec lo..."
       plan-reviewer     1       def-456         "Plan looks s..."
       ───────────────────────────────────────────────────────
       ```

     - If file does not exist or `FileNotFoundError`: print
       "No subagent activity recorded this session." and continue.
     - If a line fails JSON parse: skip it silently (partial log is still useful).
  ```

  Renumber the existing step 2 (ADR count) to step 3.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the updated `zie-retro.md` and confirm:
  - Section heading is "Subagent Activity" (exact match for test).
  - "No subagent activity" phrase is present (exact match for test).
  - "subagent-log" string is present (exact match for test).
  - Numbered steps in "รวบรวม context" are consistent.

  Run: `make test-unit` — still PASS

---

## Task 4: Document resume pattern in `/zie-implement`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `/zie-implement` contains a "Resume Subagent" documentation block.
- The block explains that agent IDs are session-scoped.
- The block explains that if the session has ended, a fresh subagent must be started.
- The block explains how to reference an agent by ID for follow-up review.
- The block is placed in the "Notes" section or a dedicated section near the end.
- Existing implement flow and steps are unmodified.

**Files:**
- Modify: `commands/zie-implement.md`
- Create: `tests/unit/test_commands_implement_resume.py`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_commands_implement_resume.py

  """Structural tests: /zie-implement must document the resume-subagent pattern."""
  import os
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "zie-implement.md"


  class TestImplementResumePattern:
      def _src(self):
          return IMPLEMENT_CMD.read_text()

      def test_resume_subagent_heading_present(self):
          assert "Resume Subagent" in self._src(), (
              "zie-implement.md must contain a 'Resume Subagent' section"
          )

      def test_session_scoped_warning_present(self):
          src = self._src()
          assert "session" in src.lower() and "agent" in src.lower(), (
              "zie-implement.md must mention session-scoped agent IDs"
          )

      def test_fresh_subagent_fallback_documented(self):
          src = self._src()
          assert "fresh" in src or "new subagent" in src or "start" in src, (
              "zie-implement.md must document what to do when session has ended"
          )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, append the following block to the "Notes" section:

  ```markdown
  ### Resume Subagent

  When a reviewer subagent completes, its agent ID is captured in the session
  subagent log (see `/zie-retro` Subagent Activity section). To continue a
  reviewer in the same context for a follow-up question, reference the agent
  by ID using `@agent:<id>` in a new message to that subagent via `SendMessage`.

  **Important:** Agent IDs are session-scoped. They are valid only within the
  current Claude Code session. If the session has ended (e.g., you closed the
  terminal or restarted Claude Code), the agent ID is no longer valid — start
  a fresh subagent instead. The subagent log in `/zie-retro` shows IDs from
  the current session only; previous sessions are cleaned up by
  `session-cleanup.py`.

  **When to resume vs. start fresh:**
  - Resume: same session, same context, follow-up question on the same artifact.
  - Start fresh: new session, new artifact, or the original agent's context
    is no longer relevant.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the updated `zie-implement.md` and confirm:
  - "Resume Subagent" heading is present (exact match for test).
  - "session" and "agent" appear in proximity.
  - "fresh" or equivalent fallback language is present.
  - The addition is in Notes and does not alter the main task loop steps.

  Run: `make test-unit` — still PASS

---

## Dependency Order

```
Task 4  ──────────────────────────────────────────────┐
Task 1  ──┬──────────────────────────────────────────►│ (all independent — run in parallel)
Task 2  ──┘ (depends_on: Task 1, but Task 1 is quick) │
Task 3  ──────────────────────────────────────────────┘
```

Tasks 1, 3, and 4 have no shared dependencies. Task 2 depends on Task 1 (the script must exist before registering it, to allow manual smoke-test). In practice all four can be implemented sequentially without issue.

---

## Final Checklist

- [ ] `make test-unit` passes with all new test classes green
- [ ] `hooks/subagent-stop.py` exits 0 on every code path
- [ ] `hooks/hooks.json` is valid JSON (`python3 -c "import json; json.load(open('hooks/hooks.json'))"`)
- [ ] No `.tmp` file artifacts left by the hook (append mode, no tmp rename)
- [ ] `commands/zie-retro.md` contains "Subagent Activity" section
- [ ] `commands/zie-implement.md` contains "Resume Subagent" block
- [ ] No secrets or API keys introduced
- [ ] `session-cleanup.py` unchanged — existing glob covers new log name automatically

---

*Commit: `git add hooks/subagent-stop.py hooks/hooks.json commands/zie-retro.md commands/zie-implement.md tests/unit/test_hooks_subagent_stop.py tests/unit/test_hooks_json.py tests/unit/test_commands_retro_subagent.py tests/unit/test_commands_implement_resume.py && git commit -m "feat: subagent-lifecycle-hooks — SubagentStop capture + resume pattern"`*
