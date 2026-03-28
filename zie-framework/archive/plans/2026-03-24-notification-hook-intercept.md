---
approved: true
approved_at: 2026-03-24
backlog: backlog/notification-hook-intercept.md
spec: specs/2026-03-24-notification-hook-intercept-design.md
---

# Notification Hook — Intercept Permission Dialogs — Implementation Plan

**Goal:** Add `hooks/notification-log.py` — an async `Notification` hook that
logs `permission_prompt` and `idle_prompt` events to project-scoped `/tmp`
files, and injects `additionalContext` when the same permission has been
prompted 3 or more times in a session.

**Architecture:** Single hook script handles both `notification_type` values
via an internal branch. Two entries in `hooks.json` under `"Notification"` both
point to the same script. The hook reuses `read_event`, `get_cwd`,
`project_tmp_path`, and `safe_write_tmp` from `utils.py` — no changes to
`utils.py` are needed.

**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/notification-log.py` | New Notification hook — log + repeat-detect |
| Modify | `hooks/hooks.json` | Add two `Notification` matchers |
| Create | `tests/unit/test_hooks_notification_log.py` | Full unit-test coverage |

---

## Task 1: Create `hooks/notification-log.py`

<!-- depends_on: none -->

**Acceptance Criteria:**

- Hook exits 0 on all paths (no unhandled exceptions, no non-zero exit codes).
- `permission_prompt` events: appends a `{"ts": "<ISO-8601 UTC>", "msg": "..."}` record to `/tmp/zie-<project>-permission-log`.
- On the 3rd (and subsequent) occurrence of the same `msg` in that log, prints `{"additionalContext": "..."}` JSON to stdout.
- `idle_prompt` events: appends a record to `/tmp/zie-<project>-idle-log`; no stdout.
- Unknown `notification_type` values: exits 0 silently, no file writes.
- Missing `message` key: treated as empty string `""`.
- Corrupted log file: resets to empty list, continues.
- Symlink at log path: `safe_write_tmp` refuses and returns False; hook logs stderr warning and exits 0.
- All inner I/O errors logged to stderr as `[zie-framework] notification-log: <error>`.

**Files:**

- Create: `hooks/notification-log.py`
- Create: `tests/unit/test_hooks_notification_log.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_notification_log.py

  """Tests for hooks/notification-log.py"""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  import pytest

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "notification-log.py")


  def run_hook(event: dict, project_name: str, env_overrides: dict | None = None):
      """Run the hook with the given event dict and CLAUDE_CWD set to a fake project dir."""
      env = {
          **os.environ,
          "CLAUDE_CWD": f"/tmp/fake-project-{project_name}",
      }
      if env_overrides:
          env.update(env_overrides)
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  def tmp_log_path(name: str, project: str) -> Path:
      """Mirror project_tmp_path logic for test assertions."""
      import re
      safe = re.sub(r"[^a-zA-Z0-9]", "-", project)
      return Path(f"/tmp/zie-{safe}-{name}")


  # ---------------------------------------------------------------------------
  # TestPermissionPromptLogging
  # ---------------------------------------------------------------------------

  class TestPermissionPromptLogging:
      def test_log_file_created_on_first_event(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Read file /etc/hosts"},
              project,
          )

          assert log.exists(), f"permission-log not created at {log}"

      def test_log_record_has_ts_and_msg(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Read file /etc/hosts"},
              project,
          )

          records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
          assert len(records) == 1
          assert records[0]["msg"] == "Read file /etc/hosts"
          assert "ts" in records[0]

      def test_log_accumulates_multiple_events(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          for _ in range(2):
              run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )

          records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
          assert len(records) == 2

      def test_no_stdout_on_first_two_occurrences(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          for _ in range(2):
              r = run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )
              assert r.stdout.strip() == "", f"Unexpected stdout on occurrence: {r.stdout!r}"

      def test_additional_context_injected_on_third_occurrence(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          # First two — no context
          for _ in range(2):
              run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )

          # Third — context must be injected
          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Read file /etc/hosts"},
              project,
          )
          assert r.stdout.strip() != "", "additionalContext expected on 3rd occurrence"
          payload = json.loads(r.stdout.strip())
          assert "additionalContext" in payload
          assert "/zie-permissions" in payload["additionalContext"]

      def test_additional_context_injected_on_fourth_and_beyond(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          for _ in range(3):
              run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )

          # Fourth occurrence — still injects
          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Read file /etc/hosts"},
              project,
          )
          payload = json.loads(r.stdout.strip())
          assert "additionalContext" in payload

      def test_count_is_per_message_not_total(self, tmp_path):
          """Different messages do not cross-contaminate counts."""
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          for _ in range(2):
              run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )
          # Different message — should NOT trigger context even though total log has 2+ entries
          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Write file /tmp/out"},
              project,
          )
          assert r.stdout.strip() == "", "Different message must not trigger context injection"

      def test_missing_message_key_treated_as_empty_string(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)

          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt"},
              project,
          )
          assert r.returncode == 0
          records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
          assert records[0]["msg"] == ""

      def test_corrupted_log_resets_to_empty(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.write_text("not valid json\nmore garbage\n")

          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "some permission"},
              project,
          )
          assert r.returncode == 0
          records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
          # After reset, only the new record should be present
          assert len(records) == 1
          assert records[0]["msg"] == "some permission"


  # ---------------------------------------------------------------------------
  # TestIdlePromptLogging
  # ---------------------------------------------------------------------------

  class TestIdlePromptLogging:
      def test_idle_log_created(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("idle-log", project)
          log.unlink(missing_ok=True)

          run_hook(
              {"event": "Notification", "notification_type": "idle_prompt",
               "message": "Session has been idle"},
              project,
          )
          assert log.exists(), f"idle-log not created at {log}"

      def test_idle_log_record_has_ts_and_msg(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("idle-log", project)
          log.unlink(missing_ok=True)

          run_hook(
              {"event": "Notification", "notification_type": "idle_prompt",
               "message": "Session has been idle"},
              project,
          )
          records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
          assert records[0]["msg"] == "Session has been idle"
          assert "ts" in records[0]

      def test_idle_no_stdout(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("idle-log", project)
          log.unlink(missing_ok=True)

          r = run_hook(
              {"event": "Notification", "notification_type": "idle_prompt",
               "message": "Session has been idle"},
              project,
          )
          assert r.stdout.strip() == "", f"idle_prompt must not produce stdout: {r.stdout!r}"


  # ---------------------------------------------------------------------------
  # TestUnknownNotificationType
  # ---------------------------------------------------------------------------

  class TestUnknownNotificationType:
      def test_unknown_type_exits_zero_no_output(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          r = run_hook(
              {"event": "Notification", "notification_type": "auth_success",
               "message": "Login ok"},
              project,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_missing_notification_type_exits_zero(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          r = run_hook({"event": "Notification"}, project)
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  # ---------------------------------------------------------------------------
  # TestGuardrails
  # ---------------------------------------------------------------------------

  class TestGuardrails:
      def test_bad_stdin_exits_zero(self):
          """Malformed JSON on stdin must not crash the hook."""
          r = subprocess.run(
              [sys.executable, HOOK],
              input="not json",
              capture_output=True,
              text=True,
          )
          assert r.returncode == 0

      def test_always_exits_zero(self, tmp_path):
          project = f"testproj-{tmp_path.name}"
          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "Read file /etc/hosts"},
              project,
          )
          assert r.returncode == 0

      def test_symlink_at_log_path_logs_stderr_exits_zero(self, tmp_path):
          """If the log path is a symlink, safe_write_tmp refuses and hook still exits 0."""
          project = f"testproj-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          log.unlink(missing_ok=True)
          # Create a symlink pointing somewhere harmless
          target = tmp_path / "real_file.txt"
          target.write_text("")
          log.symlink_to(target)

          try:
              r = run_hook(
                  {"event": "Notification", "notification_type": "permission_prompt",
                   "message": "Read file /etc/hosts"},
                  project,
              )
              assert r.returncode == 0
          finally:
              log.unlink(missing_ok=True)

      def test_two_tier_error_pattern_in_source(self):
          """Hook source must contain the two-tier error pattern: outer except + inner except."""
          source = Path(HOOK).read_text()
          assert "sys.exit(0)" in source, "Outer guard must call sys.exit(0) on parse failure"
          assert "[zie-framework] notification-log:" in source, (
              "Inner operations must log to stderr with [zie-framework] notification-log: prefix"
          )
  ```

  Run: `make test-unit` — must FAIL (hook file does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/notification-log.py

  #!/usr/bin/env python3
  """Notification hook — log permission_prompt and idle_prompt events.

  Injects additionalContext when the same permission has been prompted
  3 or more times in the current session.
  """
  import json
  import os
  import sys
  from datetime import datetime, timezone

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import get_cwd, project_tmp_path, read_event, safe_write_tmp

  # --- Outer guard: parse event; any failure exits 0 silently ---
  try:
      event = read_event()
      notification_type = event.get("notification_type", "")
      if notification_type not in ("permission_prompt", "idle_prompt"):
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # --- Inner operations: file I/O; errors are logged, hook still exits 0 ---
  try:
      message = event.get("message", "")
      project = get_cwd().name

      if notification_type == "permission_prompt":
          log_path = project_tmp_path("permission-log", project)

          # Read existing records
          records = []
          if log_path.exists():
              try:
                  for line in log_path.read_text().splitlines():
                      line = line.strip()
                      if line:
                          records.append(json.loads(line))
              except Exception:
                  records = []

          # Append new record
          ts = datetime.now(timezone.utc).isoformat()
          records.append({"ts": ts, "msg": message})

          # Write atomically
          content = "\n".join(json.dumps(r) for r in records) + "\n"
          ok = safe_write_tmp(log_path, content)
          if not ok:
              print(
                  f"[zie-framework] notification-log: failed to write {log_path}",
                  file=sys.stderr,
              )

          # Count occurrences of this exact message
          count = sum(1 for r in records if r.get("msg") == message)
          if count >= 3:
              print(json.dumps({
                  "additionalContext": (
                      "This permission has been asked 3+ times this session. "
                      "Run /zie-permissions to add it to the allow list."
                  )
              }))

      elif notification_type == "idle_prompt":
          log_path = project_tmp_path("idle-log", project)

          # Read existing records
          records = []
          if log_path.exists():
              try:
                  for line in log_path.read_text().splitlines():
                      line = line.strip()
                      if line:
                          records.append(json.loads(line))
              except Exception:
                  records = []

          # Append new record
          ts = datetime.now(timezone.utc).isoformat()
          records.append({"ts": ts, "msg": message})

          content = "\n".join(json.dumps(r) for r in records) + "\n"
          ok = safe_write_tmp(log_path, content)
          if not ok:
              print(
                  f"[zie-framework] notification-log: failed to write {log_path}",
                  file=sys.stderr,
              )

  except Exception as e:
      print(f"[zie-framework] notification-log: {e}", file=sys.stderr)
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Extract the shared read-append-write sequence into an inline helper `_append_log(log_path, message)` that returns the updated records list. This removes the duplication between the `permission_prompt` and `idle_prompt` branches while keeping all logic in the single file.

  ```python
  # hooks/notification-log.py — refactored inner section

  def _read_records(log_path):
      """Read newline-delimited JSON records from log_path.

      Returns [] if the file is absent or any line fails to parse (full reset).
      """
      if not log_path.exists():
          return []
      records = []
      try:
          for line in log_path.read_text().splitlines():
              line = line.strip()
              if line:
                  records.append(json.loads(line))
      except Exception:
          return []
      return records


  def _append_and_write(log_path, message):
      """Append a timestamped record to log_path and write atomically.

      Returns the updated records list (including the new entry).
      Logs to stderr if safe_write_tmp refuses the write.
      """
      records = _read_records(log_path)
      ts = datetime.now(timezone.utc).isoformat()
      records.append({"ts": ts, "msg": message})
      content = "\n".join(json.dumps(r) for r in records) + "\n"
      ok = safe_write_tmp(log_path, content)
      if not ok:
          print(
              f"[zie-framework] notification-log: failed to write {log_path}",
              file=sys.stderr,
          )
      return records
  ```

  The `permission_prompt` branch becomes:

  ```python
  log_path = project_tmp_path("permission-log", project)
  records = _append_and_write(log_path, message)
  count = sum(1 for r in records if r.get("msg") == message)
  if count >= 3:
      print(json.dumps({
          "additionalContext": (
              "This permission has been asked 3+ times this session. "
              "Run /zie-permissions to add it to the allow list."
          )
      }))
  ```

  The `idle_prompt` branch becomes:

  ```python
  log_path = project_tmp_path("idle-log", project)
  _append_and_write(log_path, message)
  ```

  Run: `make test-unit` — must still PASS with zero changes to the test file.

---

## Task 2: Register Notification hooks in `hooks.json` (`permission_prompt` and `idle_prompt`)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `hooks.json` contains a top-level `"Notification"` key under `"hooks"`.
- Two matcher entries: one for `"permission_prompt"`, one for `"idle_prompt"`.
- Both point to `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/notification-log.py"`.
- All existing hook entries (`SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PreToolUse`, `Stop`) are preserved without modification.
- `_hook_output_protocol` comment block is updated to document the `Notification` output format.

**Files:**

- Modify: `hooks/hooks.json`

---

- [ ] **Step 1: Write failing tests (RED)**

  Add a new test class to `tests/unit/test_hooks_notification_log.py`:

  ```python
  # tests/unit/test_hooks_notification_log.py — append at end of file

  class TestHooksJsonRegistration:
      HOOKS_JSON = Path(REPO_ROOT) / "hooks" / "hooks.json"

      def _load(self):
          return json.loads(self.HOOKS_JSON.read_text())

      def test_notification_key_exists(self):
          data = self._load()
          assert "Notification" in data["hooks"], (
              "hooks.json must have a 'Notification' key under 'hooks'"
          )

      def test_permission_prompt_matcher_registered(self):
          data = self._load()
          matchers = [entry.get("matcher") for entry in data["hooks"]["Notification"]]
          assert "permission_prompt" in matchers, (
              "Notification hooks must include a 'permission_prompt' matcher"
          )

      def test_idle_prompt_matcher_registered(self):
          data = self._load()
          matchers = [entry.get("matcher") for entry in data["hooks"]["Notification"]]
          assert "idle_prompt" in matchers, (
              "Notification hooks must include an 'idle_prompt' matcher"
          )

      def test_both_matchers_point_to_notification_log(self):
          data = self._load()
          for entry in data["hooks"]["Notification"]:
              for hook in entry.get("hooks", []):
                  assert "notification-log.py" in hook.get("command", ""), (
                      f"Notification hook entry must reference notification-log.py: {hook}"
                  )

      def test_existing_events_unchanged(self):
          data = self._load()
          hooks = data["hooks"]
          for event in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
              assert event in hooks, f"Existing event '{event}' must still be present in hooks.json"

      def test_notification_output_protocol_documented(self):
          data = self._load()
          protocol = data.get("_hook_output_protocol", {})
          assert "Notification" in protocol, (
              "_hook_output_protocol must document the Notification output format"
          )
  ```

  Run: `make test-unit` — must FAIL (`"Notification"` key absent from hooks.json)

---

- [ ] **Step 2: Implement (GREEN)**

  Edit `hooks/hooks.json` to add the `Notification` entries and update `_hook_output_protocol`:

  ```json
  {
    "_hook_output_protocol": {
      "SessionStart": "plain text printed to stdout — injected as session context",
      "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
      "PostToolUse": "plain text warnings/status printed to stdout",
      "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
      "Stop": "no output required; side-effects only (file writes, API calls)",
      "Notification": "JSON {\"additionalContext\": \"...\"} printed to stdout to inject context; empty stdout to pass through"
    },
    "hooks": {
      "SessionStart": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-resume.py\""
            }
          ]
        }
      ],
      "UserPromptSubmit": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-detect.py\""
            }
          ]
        }
      ],
      "PostToolUse": [
        {
          "matcher": "Edit|Write",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/auto-test.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/wip-checkpoint.py\""
            }
          ]
        }
      ],
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
            }
          ]
        }
      ],
      "Stop": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
            }
          ]
        }
      ],
      "Notification": [
        {
          "matcher": "permission_prompt",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/notification-log.py\""
            }
          ]
        },
        {
          "matcher": "idle_prompt",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/notification-log.py\""
            }
          ]
        }
      ]
    }
  }
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Verify no duplicate keys exist in `hooks.json` by loading it with `json.loads` in a scratch run. Confirm the `_hook_output_protocol` block is at the top of the file for readability. No structural code changes required.

  Run: `make test-unit` — must still PASS

---

## Commit

```
git add hooks/notification-log.py hooks/hooks.json tests/unit/test_hooks_notification_log.py
git commit -m "feat: notification-log hook — log permission/idle events, inject repeat-prompt context"
```
