---
approved: false
approved_at:
backlog: backlog/proactive-compact-hint.md
---

# Proactive Compact Hint — Implementation Plan

**Goal:** Add a Stop hook that prints a `/compact` reminder to stdout when context usage meets or exceeds a configurable threshold (default 80%).
**Architecture:** New `hooks/compact-hint.py` registered in `hooks/hooks.json` under the `Stop` event. Reads `context_window.current_tokens / max_tokens` from the hook event JSON; compares against `compact_hint_threshold` from `.config` (via `load_config()`); prints a plain-text hint to stdout when triggered. Follows the two-tier outer-guard / inner-operations pattern. All paths exit 0.
**Tech Stack:** Python 3, `hooks/utils.py` (`read_event`, `get_cwd`, `load_config`), `hooks/hooks.json`, `CLAUDE.md`.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `tests/unit/test_hooks_compact_hint.py` | Unit tests — subprocess-driven, covers all AC |
| Create | `hooks/compact-hint.py` | Stop hook — reads context_window, prints hint when threshold met |
| Modify | `hooks/hooks.json` | Register `compact-hint.py` under the `Stop` event |
| Modify | `CLAUDE.md` | Add `compact_hint_threshold` row to Hook Configuration table |

## Task Sizing Check

- 5 tasks total → M plan (4–7), correctly sized
- T1 (tests) and T2 (hook) share no output files → parallel allowed
- T3 and T4 modify different files → parallel allowed
- T5 depends on T1–T4 → must run last

---

## Task 1: Write Failing Tests (RED)

**Acceptance Criteria:**
- All 7 test cases exist in `tests/unit/test_hooks_compact_hint.py`
- `make test-unit` reports each test as FAILED (hook does not exist yet)
- No test imports the hook directly — all use subprocess

**Files:**
- Create: `tests/unit/test_hooks_compact_hint.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  """Tests for hooks/compact-hint.py"""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "compact-hint.py")


  def run_hook(tmp_cwd, event=None, config=None, env_overrides=None):
      if event is None:
          event = {}
      env = {**os.environ, "CLAUDE_CWD": str(tmp_cwd)}
      if env_overrides:
          env.update(env_overrides)
      if config is not None:
          zf = Path(tmp_cwd) / "zie-framework"
          zf.mkdir(parents=True, exist_ok=True)
          (zf / ".config").write_text(json.dumps(config))
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  def make_cwd(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True, exist_ok=True)
      return tmp_path


  class TestHintPrinted:
      def test_hint_printed_when_above_threshold(self, tmp_path):
          """80% threshold (default); event at 85% → hint appears in stdout."""
          cwd = make_cwd(tmp_path)
          event = {"context_window": {"current_tokens": 850, "max_tokens": 1000}}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert "[zie-framework] Context at 85%" in r.stdout
          assert "/compact" in r.stdout

      def test_hint_printed_at_exactly_threshold(self, tmp_path):
          """Boundary: event at exactly 80% → hint printed (>= not >)."""
          cwd = make_cwd(tmp_path)
          event = {"context_window": {"current_tokens": 800, "max_tokens": 1000}}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert "[zie-framework] Context at 80%" in r.stdout


  class TestNoHint:
      def test_no_hint_when_below_threshold(self, tmp_path):
          """Event at 70% with default threshold 0.8 → no stdout output."""
          cwd = make_cwd(tmp_path)
          event = {"context_window": {"current_tokens": 700, "max_tokens": 1000}}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_graceful_skip_when_context_window_missing(self, tmp_path):
          """Event with no context_window field → exit 0, no stdout."""
          cwd = make_cwd(tmp_path)
          event = {"session_id": "abc123"}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_graceful_skip_when_tokens_missing(self, tmp_path):
          """context_window present but empty dict → exit 0, no stdout."""
          cwd = make_cwd(tmp_path)
          event = {"context_window": {}}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_stop_hook_active_guard(self, tmp_path):
          """stop_hook_active=true → exit 0 immediately, no hint."""
          cwd = make_cwd(tmp_path)
          event = {
              "stop_hook_active": True,
              "context_window": {"current_tokens": 950, "max_tokens": 1000},
          }
          r = run_hook(cwd, event=event)
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  class TestThresholdConfig:
      def test_threshold_configurable(self, tmp_path):
          """compact_hint_threshold=0.9 in .config → no hint at 85%, hint at 91%."""
          cwd = make_cwd(tmp_path)
          config = {"compact_hint_threshold": 0.9}

          # 85% — below custom threshold → no hint
          event_85 = {"context_window": {"current_tokens": 850, "max_tokens": 1000}}
          r85 = run_hook(cwd, event=event_85, config=config)
          assert r85.returncode == 0
          assert r85.stdout.strip() == ""

          # 91% — above custom threshold → hint
          event_91 = {"context_window": {"current_tokens": 910, "max_tokens": 1000}}
          r91 = run_hook(cwd, event=event_91, config=config)
          assert r91.returncode == 0
          assert "[zie-framework] Context at 91%" in r91.stdout


  class TestAlwaysExitsZero:
      def test_always_exits_zero_when_hint_printed(self, tmp_path):
          """Even when hint is printed, exit code must be 0."""
          cwd = make_cwd(tmp_path)
          event = {"context_window": {"current_tokens": 900, "max_tokens": 1000}}
          r = run_hook(cwd, event=event)
          assert r.returncode == 0

      def test_always_exits_zero_on_malformed_stdin(self, tmp_path):
          """Malformed JSON stdin → outer guard exits 0."""
          cwd = make_cwd(tmp_path)
          env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
          r = subprocess.run(
              [sys.executable, HOOK],
              input="not valid json{{",
              capture_output=True,
              text=True,
              env=env,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  class TestHooksJsonRegistration:
      def test_compact_hint_registered_in_hooks_json(self):
          hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
          data = json.loads(hooks_json.read_text())
          stop_entries = data.get("hooks", {}).get("Stop", [])
          commands = [
              h["command"]
              for entry in stop_entries
              for h in entry.get("hooks", [])
              if h.get("type") == "command"
          ]
          assert any("compact-hint.py" in cmd for cmd in commands), (
              "hooks/hooks.json Stop event must reference compact-hint.py"
          )
  ```

  Run: `make test-unit` — must FAIL (hook file does not exist yet)

- [ ] **Step 2: Implement (GREEN)**
  No implementation in this task — tests fail as expected.

- [ ] **Step 3: Refactor**
  N/A — test-only task.

---

## Task 2: Implement compact-hint.py (GREEN)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- All tests in Task 1 pass
- Hook follows two-tier pattern (outer guard → inner operations)
- No exception propagates; all paths exit 0
- Hint message format exactly matches spec: `[zie-framework] Context at {pct}% — consider running /compact to free space before continuing.`

**Files:**
- Create: `hooks/compact-hint.py`

- [ ] **Step 1: Write failing tests (RED)**
  Tests already written in Task 1. Confirm `make test-unit` still FAILS.

- [ ] **Step 2: Implement (GREEN)**

  ```python
  #!/usr/bin/env python3
  """Stop hook — print a /compact hint when context usage meets the threshold.

  Reads context_window.current_tokens / max_tokens from the Stop event JSON.
  If the ratio >= compact_hint_threshold (default 0.8 from .config), prints
  a plain-text hint to stdout. Plain text on stdout is surfaced to Claude as
  informational context — no decision:block needed.

  Always exits 0 (ADR-003).
  Infinite-loop guard: exits immediately when stop_hook_active is truthy.
  """
  import os
  import sys

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import get_cwd, load_config, read_event

  # ---------------------------------------------------------------------------
  # Outer guard — parse stdin; never block Claude on failure
  # ---------------------------------------------------------------------------
  try:
      event = read_event()
      if event.get("stop_hook_active"):
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # ---------------------------------------------------------------------------
  # Inner operations — check context usage; print hint when threshold met
  # ---------------------------------------------------------------------------
  try:
      cwd = get_cwd()
      config = load_config(cwd)
      threshold = config.get("compact_hint_threshold", 0.8)

      context_window = event.get("context_window")
      if not isinstance(context_window, dict):
          sys.exit(0)

      current = context_window.get("current_tokens")
      max_tokens = context_window.get("max_tokens")
      if current is None or not max_tokens:
          sys.exit(0)

      pct = current / max_tokens
      if pct >= threshold:
          print(
              f"[zie-framework] Context at {int(pct * 100)}%"
              " \u2014 consider running /compact to free space before continuing."
          )
  except Exception as e:
      print(f"[zie-framework] compact-hint: {e}", file=sys.stderr)
  sys.exit(0)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify no dead branches. Confirm `threshold = config.get("compact_hint_threshold", 0.8)` — `load_config()` does not define this key in `CONFIG_SCHEMA`, so `.get()` with a default is correct (same pattern as `safety_check_mode`).
  Run: `make test-unit` — still PASS

---

## Task 3: Register in hooks.json

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `hooks/hooks.json` `Stop` block includes `compact-hint.py` entry
- `TestHooksJsonRegistration.test_compact_hint_registered_in_hooks_json` passes
- Hook runs as a regular (non-background) command — hint must reach Claude before session continues

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Write failing tests (RED)**
  `TestHooksJsonRegistration` already written in Task 1 and currently failing. Confirm.

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/hooks.json`, add `compact-hint.py` to the existing `Stop` hooks array (after `stop-guard.py`, before the background hooks):

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
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/compact-hint.py\""
        },
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\"",
          "background": true
        },
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\"",
          "background": true
        }
      ]
    }
  ]
  ```

  Run: `make test-unit` — `TestHooksJsonRegistration` must PASS

- [ ] **Step 3: Refactor**
  Validate full `hooks.json` parses as valid JSON: `python3 -c "import json; json.load(open('hooks/hooks.json'))"` — no error.
  Run: `make test-unit` — still PASS

---

## Task 4: Document compact_hint_threshold in CLAUDE.md

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `CLAUDE.md` Hook Configuration table contains `compact_hint_threshold` row
- Row matches spec: default `0.8`, type `float`, description explains 0.0–1.0 range and `1.0` disables

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test for CLAUDE.md content — verified manually. Proceed to implement.

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, inside the Hook Configuration table, add this row after the `auto_test_timeout_ms` entry:

  ```markdown
  | `compact_hint_threshold` | `0.8` | `float` | Usage fraction (0.0–1.0) at which the Stop hook prints the `/compact` hint. Set to `1.0` to disable. |
  ```

  Run: `make lint` — must PASS (markdown lint)

- [ ] **Step 3: Refactor**
  Confirm row is aligned with surrounding table columns.
  Run: `make lint` — still PASS

---

## Task 5: Full CI Gate (REFACTOR)

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- `make test-ci` exits 0
- Coverage gate passes
- All 7 compact-hint tests pass
- No regressions in existing test suite

**Files:**
- No new files

- [ ] **Step 1: Write failing tests (RED)**
  N/A — all tests written in Task 1.

- [ ] **Step 2: Implement (GREEN)**
  N/A — all implementation done in Tasks 2–4.

- [ ] **Step 3: Refactor**

  ```bash
  make test-ci
  ```

  Expected output:
  ```
  ...
  tests/unit/test_hooks_compact_hint.py ......... [100%]
  ...
  PASSED
  Coverage: XX% ≥ gate
  ```

  If any test fails, diagnose and fix before proceeding.
  Run: `make test-ci` — must exit 0

---
