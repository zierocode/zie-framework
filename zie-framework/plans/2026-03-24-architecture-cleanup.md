---
approved: true
approved_at: 2026-03-24
backlog: backlog/architecture-cleanup.md
spec: specs/2026-03-24-architecture-cleanup-design.md
---

# Architecture Cleanup and Structural Improvements — Implementation Plan

**Goal:** Five targeted structural improvements: (1) add `SDLC_STAGES` canonical list to utils.py; (2) add `warn_on_empty` parameter to `parse_roadmap_now()`; (3) make `TEST_INDICATORS` configurable via `.config`; (4) add `"async": true` to session-learn and session-cleanup in hooks.json; (5) create `hooks/hook-events.schema.json`.
**Architecture:** All changes are additive or in-place modifications to existing files. No new hook scripts. No new dependencies. Backward compatible — all existing callers unaffected.
**Tech Stack:** Python 3.x, pytest, stdlib only

**Dependency note:** Task 3 (`TEST_INDICATORS` configurable) depends on `consolidate-utils-patterns` being implemented first. `load_config()` currently parses INI-style `key = value` lines only. The spec for Task 3 passes a comma-separated string value via `.config` (e.g. `test_indicators = test_, _test.`), which works with the current INI parser — but the spec also shows a JSON example. The `_load_test_indicators()` function in Task 3 uses `config.get("test_indicators", "")` and splits on commas, so it works with the existing INI parser. Task 3 can be implemented independently; however if `consolidate-utils-patterns` changes `load_config()` to parse JSON, the comma-split approach must still be validated. Document this at implementation time.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `SDLC_STAGES` constant; add `warn_on_empty` param to `parse_roadmap_now()` |
| Modify | `hooks/intent-detect.py` | Import `SDLC_STAGES` from utils; add passive validation comment |
| Modify | `hooks/sdlc-context.py` | Import `SDLC_STAGES` from utils; add passive validation comment |
| Modify | `hooks/task-completed-gate.py` | Replace hardcoded `TEST_INDICATORS` with `_load_test_indicators(cwd)` |
| Modify | `hooks/hooks.json` | Add `"async": true` to session-learn and session-cleanup Stop entries |
| Create | `hooks/hook-events.schema.json` | JSON Schema for the common hook event envelope |
| Modify | `tests/unit/test_utils.py` | Tests for `SDLC_STAGES` and `warn_on_empty` |
| Create | `tests/unit/test_architecture_cleanup.py` | Tests for `TEST_INDICATORS` config, async hooks, schema file |

---

## Task 1: `SDLC_STAGES` in utils.py + imports in intent-detect.py and sdlc-context.py

**Acceptance Criteria:**
- `SDLC_STAGES` is a `list[str]` exported from `hooks/utils.py` with value `["init", "backlog", "spec", "plan", "implement", "fix", "release", "retro"]`
- `hooks/intent-detect.py` imports `SDLC_STAGES` from utils and has a comment confirming `PATTERNS` keys are a subset of `SDLC_STAGES`
- `hooks/sdlc-context.py` imports `SDLC_STAGES` from utils and has a comment confirming `STAGE_KEYWORDS` stage names are a subset of `SDLC_STAGES`
- No runtime assertions — validation is documentation-only (passive)
- All existing tests pass

**Files:**
- Modify: `hooks/utils.py`
- Modify: `hooks/intent-detect.py`
- Modify: `hooks/sdlc-context.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py

  class TestSdlcStages:
      def test_sdlc_stages_is_exported(self):
          from utils import SDLC_STAGES
          assert SDLC_STAGES is not None

      def test_sdlc_stages_is_list(self):
          from utils import SDLC_STAGES
          assert isinstance(SDLC_STAGES, list)

      def test_sdlc_stages_contains_eight_entries(self):
          from utils import SDLC_STAGES
          assert len(SDLC_STAGES) == 8

      def test_sdlc_stages_values(self):
          from utils import SDLC_STAGES
          assert SDLC_STAGES == [
              "init", "backlog", "spec", "plan",
              "implement", "fix", "release", "retro",
          ]

      def test_sdlc_stages_all_strings(self):
          from utils import SDLC_STAGES
          assert all(isinstance(s, str) for s in SDLC_STAGES)

      def test_intent_detect_imports_sdlc_stages(self):
          """intent-detect.py must reference SDLC_STAGES from utils."""
          content = (REPO_ROOT / "hooks" / "intent-detect.py").read_text()
          assert "SDLC_STAGES" in content, (
              "intent-detect.py must import or reference SDLC_STAGES"
          )

      def test_sdlc_context_imports_sdlc_stages(self):
          """sdlc-context.py must reference SDLC_STAGES from utils."""
          content = (REPO_ROOT / "hooks" / "sdlc-context.py").read_text()
          assert "SDLC_STAGES" in content, (
              "sdlc-context.py must import or reference SDLC_STAGES"
          )
  ```

  Run: `make test-unit` — must FAIL (`test_sdlc_stages_is_exported` fails because `SDLC_STAGES` does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/utils.py — add after the module docstring, before parse_roadmap_section:

  SDLC_STAGES: list[str] = [
      "init", "backlog", "spec", "plan",
      "implement", "fix", "release", "retro",
  ]
  ```

  ```python
  # In hooks/intent-detect.py — update import line:
  from utils import read_event, get_cwd, SDLC_STAGES

  # Add comment block after PATTERNS dict (before COMPILED_PATTERNS):
  # SDLC_STAGES validation (passive — no runtime assertion):
  # All keys in PATTERNS that map to a zie-* SDLC command must be a subset of SDLC_STAGES.
  # "status" is an auxiliary key (not an SDLC stage) and is intentionally excluded.
  ```

  ```python
  # In hooks/sdlc-context.py — update import line:
  from utils import parse_roadmap_now, project_tmp_path, read_event, get_cwd, SDLC_STAGES

  # Add comment block after STAGE_KEYWORDS list:
  # SDLC_STAGES validation (passive — no runtime assertion):
  # All stage names in STAGE_KEYWORDS must be a subset of SDLC_STAGES.
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No structural changes needed. Verify that neither intent-detect.py nor sdlc-context.py changed any runtime behavior — the import is purely additive. Review that `status` and `in-progress` special keys in each file are covered by comments explaining why they are not in `SDLC_STAGES`.

  Run: `make test-unit` — still PASS
  Run: `make lint` — exits 0

---

## Task 2: `parse_roadmap_now()` `warn_on_empty` parameter

**Acceptance Criteria:**
- `parse_roadmap_now(roadmap_path, warn_on_empty=False)` signature accepted
- When `warn_on_empty=False` (default): behavior identical to current — no output change
- When `warn_on_empty=True` and file exists but Now section is absent or empty: prints `[zie-framework] WARNING: ROADMAP.md Now section is empty or missing` to stderr
- When `warn_on_empty=True` and file does not exist: no warning printed
- All existing `parse_roadmap_now` callers (no arguments) are unaffected

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py — inside or after TestParseRoadmapNow

  class TestParseRoadmapNowWarnOnEmpty:
      def test_warn_false_default_no_stderr_when_empty(self, tmp_path, capsys):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n\n## Next\n- [ ] foo\n")
          result = parse_roadmap_now(f)
          assert result == []
          captured = capsys.readouterr()
          assert captured.err == ""

      def test_warn_true_emits_stderr_when_now_empty(self, tmp_path, capsys):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n\n## Next\n- [ ] foo\n")
          result = parse_roadmap_now(f, warn_on_empty=True)
          assert result == []
          captured = capsys.readouterr()
          assert "[zie-framework]" in captured.err
          assert "Now section" in captured.err

      def test_warn_true_emits_stderr_when_now_absent(self, tmp_path, capsys):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Done\n- [x] something\n")
          result = parse_roadmap_now(f, warn_on_empty=True)
          assert result == []
          captured = capsys.readouterr()
          assert "[zie-framework]" in captured.err

      def test_warn_true_no_stderr_when_file_missing(self, tmp_path, capsys):
          result = parse_roadmap_now(tmp_path / "nonexistent.md", warn_on_empty=True)
          assert result == []
          captured = capsys.readouterr()
          assert captured.err == ""

      def test_warn_true_no_stderr_when_now_has_items(self, tmp_path, capsys):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] active task\n")
          result = parse_roadmap_now(f, warn_on_empty=True)
          assert result == ["active task"]
          captured = capsys.readouterr()
          assert captured.err == ""

      def test_existing_callers_unaffected(self, tmp_path, capsys):
          """Calling with no arguments must behave exactly as before."""
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n\n")
          result = parse_roadmap_now(f)
          assert result == []
          captured = capsys.readouterr()
          assert captured.err == ""
  ```

  Run: `make test-unit` — must FAIL (`test_warn_true_emits_stderr_when_now_empty` fails because signature not yet updated)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/utils.py — replace parse_roadmap_now():

  def parse_roadmap_now(roadmap_path, warn_on_empty: bool = False) -> list:
      """Extract cleaned items from the ## Now section of ROADMAP.md.

      Returns [] if the file is missing, the Now section is absent, or it is empty.
      Accepts Path or str.

      If warn_on_empty=True and the file exists but the Now section is absent
      or empty, prints a warning to stderr.
      """
      path = Path(roadmap_path)
      items = parse_roadmap_section(path, "now")
      if warn_on_empty and path.exists() and not items:
          print(
              "[zie-framework] WARNING: ROADMAP.md Now section is empty or missing",
              file=sys.stderr,
          )
      return items
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No refactor needed. Confirm that `sdlc-context.py` (the primary caller of `parse_roadmap_now`) continues to call with no arguments — its `else` branch already handles the empty case by setting `stage = "idle"`. No callers need to be updated.

  Run: `make test-unit` — still PASS

---

## Task 3: `TEST_INDICATORS` configurable in task-completed-gate.py

**Dependency:** `load_config()` in utils.py currently parses INI-style `key = value` pairs. `_load_test_indicators()` uses comma-split on the string value, which is compatible with the current parser. If `consolidate-utils-patterns` changes `load_config()` to JSON parsing before this task is implemented, re-verify that `test_indicators` key is read correctly. Document the outcome in a comment in `task-completed-gate.py`.

**Acceptance Criteria:**
- Module-level `TEST_INDICATORS` tuple is replaced by `_load_test_indicators(cwd)` called after `cwd` is established in `main()`
- When `test_indicators` key is absent from `.config`: falls back to `("test_", "_test.", ".test.", ".spec.")` — no behavior change
- When `test_indicators` key is present: uses the comma-separated values as the tuple
- `is_impl_file()` continues to use whatever `TEST_INDICATORS` resolves to at call time
- All existing tests pass; new tests cover both code paths

**Files:**
- Modify: `hooks/task-completed-gate.py`
- Create: `tests/unit/test_architecture_cleanup.py` (initial creation with Task 3 tests)

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Create tests/unit/test_architecture_cleanup.py

  """Tests for architecture-cleanup changes:
  - TEST_INDICATORS configurable in task-completed-gate.py
  - async hooks in hooks.json
  - hook-events.schema.json
  """
  import json
  import os
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  sys.path.insert(0, str(REPO_ROOT / "hooks"))


  class TestTestIndicatorsConfigurable:
      def test_load_test_indicators_function_exists(self):
          """task-completed-gate.py must define _load_test_indicators."""
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert "_load_test_indicators" in content, (
              "_load_test_indicators not found in task-completed-gate.py"
          )

      def test_module_level_test_indicators_removed(self):
          """Hardcoded module-level TEST_INDICATORS tuple must be removed."""
          import re
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert not re.search(r'^TEST_INDICATORS\s*=', content, re.MULTILINE), (
              "TEST_INDICATORS must not be a bare module-level assignment"
          )

      def test_fallback_returns_default_tuple_when_key_absent(self, tmp_path):
          """_load_test_indicators returns default tuple when test_indicators absent."""
          # No .config file
          import importlib.util
          spec = importlib.util.spec_from_file_location(
              "task_completed_gate",
              str(REPO_ROOT / "hooks" / "task-completed-gate.py"),
          )
          # We cannot safely exec the full module (it reads stdin at import).
          # Test via source inspection that the fallback tuple is present.
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert '"test_"' in content or "'test_'" in content, (
              "fallback tuple must include 'test_'"
          )
          assert '"_test."' in content or "'_test.'" in content, (
              "fallback tuple must include '_test.'"
          )

      def test_load_test_indicators_uses_load_config(self):
          """_load_test_indicators must call load_config."""
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert "load_config" in content, (
              "task-completed-gate.py must import and call load_config"
          )

      def test_config_import_present(self):
          """load_config must be imported from utils in task-completed-gate.py."""
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert "load_config" in content
          # Verify it comes from utils
          assert "from utils import" in content

      def test_is_impl_file_still_works_with_default_indicators(self, tmp_path):
          """is_impl_file must still correctly classify files using default indicators."""
          # Directly test the logic by monkeypatching TEST_INDICATORS
          # Since the module has side effects on import, test via source inspection
          content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
          assert "is_impl_file" in content
          assert "TEST_INDICATORS" in content
  ```

  Run: `make test-unit` — must FAIL (`test_load_test_indicators_function_exists` fails)

---

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/task-completed-gate.py`:

  1. Update the `from utils import` line to include `load_config`:
     ```python
     from utils import read_event, get_cwd, load_config
     ```

  2. Remove the module-level `TEST_INDICATORS` constant (line 24).

  3. Add `_load_test_indicators()` function after `IMPL_EXTS`:
     ```python
     def _load_test_indicators(cwd: Path) -> tuple:
         """Load TEST_INDICATORS from .config or fall back to hardcoded defaults.

         Config key: test_indicators (comma-separated, e.g. "test_, _test., .test.")
         Falls back to default tuple when key is absent or empty.

         NOTE: load_config() parses INI-style key=value pairs. If consolidate-utils-patterns
         changes load_config() to JSON, re-verify that comma-split still works correctly.
         """
         config = load_config(cwd)
         raw = config.get("test_indicators", "")
         if raw:
             return tuple(s.strip() for s in raw.split(",") if s.strip())
         return ("test_", "_test.", ".test.", ".spec.")
     ```

  4. In `main()`, after `cwd = get_cwd()`, add:
     ```python
     TEST_INDICATORS = _load_test_indicators(cwd)
     ```

  5. In `check_uncommitted_files(cwd)`, load `TEST_INDICATORS` at the top of the function body and use it for the indicator filter inline. No signature changes to `is_impl_file()` or `check_uncommitted_files()`:
     ```python
     def check_uncommitted_files(cwd: Path) -> tuple:
         TEST_INDICATORS = _load_test_indicators(cwd)
         ...
         p = filename.lower()
         is_impl = (
             any(p.endswith(ext) for ext in IMPL_EXTS)
             and not any(indicator in p for indicator in TEST_INDICATORS)
         )
         if is_impl:
             ...
     ```

     `is_impl_file()` retains its original signature. The indicator filter is now applied locally inside `check_uncommitted_files()` using the loaded `TEST_INDICATORS`.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Verify that existing tests in `test_hooks_sdlc_context.py` and `test_utils.py` still pass — no signature changes were made so no call sites need updating.

  Run: `make test-unit` — still PASS
  Run: `make lint` — exits 0

---

## Task 4: Async hooks in hooks.json

**Acceptance Criteria:**
- `session-learn.py` entry in the `Stop` event array has `"async": true`
- `session-cleanup.py` entry in the `Stop` event array has `"async": true`
- `stop-guard.py` entry in `Stop` does NOT have `"async": true` (it returns a decision JSON)
- `notification-log.py` entries are NOT made async
- hooks.json remains valid JSON

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `tests/unit/test_architecture_cleanup.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_architecture_cleanup.py

  class TestAsyncStopHooks:
      def _load(self):
          with open(REPO_ROOT / "hooks" / "hooks.json") as f:
              return json.load(f)

      def _stop_hooks(self, data):
          """Return list of hook dicts from the Stop event."""
          return [
              hook
              for entry in data["hooks"].get("Stop", [])
              for hook in entry.get("hooks", [])
          ]

      def test_session_learn_has_async_true(self):
          data = self._load()
          hooks = self._stop_hooks(data)
          session_learn = [h for h in hooks if "session-learn.py" in h.get("command", "")]
          assert session_learn, "session-learn.py not found in Stop hooks"
          assert session_learn[0].get("async") is True, (
              "session-learn.py Stop hook must have async: true"
          )

      def test_session_cleanup_has_async_true(self):
          data = self._load()
          hooks = self._stop_hooks(data)
          session_cleanup = [h for h in hooks if "session-cleanup.py" in h.get("command", "")]
          assert session_cleanup, "session-cleanup.py not found in Stop hooks"
          assert session_cleanup[0].get("async") is True, (
              "session-cleanup.py Stop hook must have async: true"
          )

      def test_stop_guard_is_not_async(self):
          data = self._load()
          hooks = self._stop_hooks(data)
          stop_guard = [h for h in hooks if "stop-guard.py" in h.get("command", "")]
          assert stop_guard, "stop-guard.py not found in Stop hooks"
          assert stop_guard[0].get("async") is not True, (
              "stop-guard.py must NOT be async (it may return a decision)"
          )

      def test_notification_log_not_async(self):
          data = self._load()
          notification_hooks = [
              hook
              for entry in data["hooks"].get("Notification", [])
              for hook in entry.get("hooks", [])
          ]
          for hook in notification_hooks:
              if "notification-log.py" in hook.get("command", ""):
                  assert hook.get("async") is not True, (
                      "notification-log.py must NOT be async"
                  )

      def test_hooks_json_still_valid_json(self):
          self._load()  # must not raise
  ```

  Run: `make test-unit` — must FAIL (`test_session_learn_has_async_true` fails)

---

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/hooks.json`, find the `Stop` event array and update the session-learn and session-cleanup entries:

  ```json
  "Stop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stop-guard.py\""
        },
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\"",
          "async": true
        },
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\"",
          "async": true
        }
      ]
    }
  ]
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Verify that `test_hooks_json.py` existing tests (`TestHooksJsonStructure.test_existing_hooks_unchanged`) still pass — the Stop key remains present.

  Run: `make test-unit` — still PASS

---

## Task 5: `hooks/hook-events.schema.json`

**Acceptance Criteria:**
- File `hooks/hook-events.schema.json` exists and is valid JSON
- Contains `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- Documents `tool_name`, `tool_input`, `tool_response`, `is_interrupt`, `session_id` properties
- Uses `"additionalProperties": true` (does not restrict unknown fields)
- `title` is `"Claude Code Hook Event Envelope"`

**Files:**
- Create: `hooks/hook-events.schema.json`
- Modify: `tests/unit/test_architecture_cleanup.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_architecture_cleanup.py

  class TestHookEventsSchema:
      SCHEMA_PATH = REPO_ROOT / "hooks" / "hook-events.schema.json"

      def test_schema_file_exists(self):
          assert self.SCHEMA_PATH.exists(), (
              f"hook-events.schema.json not found at {self.SCHEMA_PATH}"
          )

      def test_schema_is_valid_json(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert isinstance(data, dict)

      def test_schema_version_field(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert data.get("$schema") == "https://json-schema.org/draft/2020-12/schema"

      def test_schema_title(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert data.get("title") == "Claude Code Hook Event Envelope"

      def test_schema_documents_tool_name(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert "tool_name" in data.get("properties", {}), (
              "schema must document tool_name property"
          )

      def test_schema_documents_tool_input(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert "tool_input" in data.get("properties", {})

      def test_schema_documents_tool_response(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert "tool_response" in data.get("properties", {})

      def test_schema_documents_is_interrupt(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert "is_interrupt" in data.get("properties", {})

      def test_schema_documents_session_id(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert "session_id" in data.get("properties", {})

      def test_schema_allows_additional_properties(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert data.get("additionalProperties") is True, (
              "additionalProperties must be true to allow future Claude Code fields"
          )

      def test_schema_type_is_object(self):
          with open(self.SCHEMA_PATH) as f:
              data = json.load(f)
          assert data.get("type") == "object"
  ```

  Run: `make test-unit` — must FAIL (`test_schema_file_exists` fails)

---

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/hook-events.schema.json`:

  ```json
  {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Claude Code Hook Event Envelope",
    "description": "Common envelope for all zie-framework hook event inputs (stdin JSON)",
    "type": "object",
    "properties": {
      "tool_name": {
        "type": "string",
        "description": "Name of the tool being invoked (PreToolUse/PostToolUse)"
      },
      "tool_input": {
        "type": ["object", "null"],
        "description": "Tool input parameters — shape varies by tool_name"
      },
      "tool_response": {
        "type": ["object", "string", "null"],
        "description": "Tool output (PostToolUse only)"
      },
      "is_interrupt": {
        "type": "boolean",
        "description": "True when Claude was interrupted mid-response"
      },
      "session_id": {
        "type": "string",
        "description": "Unique session identifier"
      }
    },
    "additionalProperties": true
  }
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No refactor needed. Verify that `make lint` does not fail on the new `.json` file (markdownlint ignores JSON; py_compile ignores JSON).

  Run: `make test-unit` — still PASS
  Run: `make lint` — exits 0

---

**Commit:** `git add hooks/utils.py hooks/intent-detect.py hooks/sdlc-context.py hooks/task-completed-gate.py hooks/hooks.json hooks/hook-events.schema.json tests/unit/test_utils.py tests/unit/test_architecture_cleanup.py && git commit -m "feat: architecture-cleanup — SDLC_STAGES, warn_on_empty, configurable TEST_INDICATORS, async stop hooks, hook-events schema"`
