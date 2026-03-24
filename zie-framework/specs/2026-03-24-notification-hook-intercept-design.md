---
approved: true
approved_at: 2026-03-24
backlog: backlog/notification-hook-intercept.md
---

# Notification Hook — Intercept Permission Dialogs — Design Spec

**Problem:** Claude Code `permission_prompt` notifications require manual user
response every time, adding friction in implement-mode sessions where all
operations are expected safe.

**Approach:** A new async `Notification` hook (`hooks/notification-log.py`)
intercepts `permission_prompt` and `idle_prompt` events. For `permission_prompt`,
it logs each occurrence with a timestamp to a project-scoped `/tmp` file using
the existing `project_tmp_path` + `safe_write_tmp` utilities. On the third
occurrence of the same permission within a session it returns `additionalContext`
advising the user to run `/zie-permissions`. The `idle_prompt` matcher logs idle
events to a separate file for session analytics without returning any context.

**Components:**
- `hooks/notification-log.py` — new hook (Notification event, async: true)
- `hooks/hooks.json` — add two new `Notification` matchers
- `hooks/utils.py` — no changes required; reuses `project_tmp_path`,
  `safe_write_tmp`, `read_event`, `get_cwd`
- `tests/test_notification_log.py` — new unit test file

---

**Data Flow:**

1. Claude Code fires a `Notification` event and writes JSON to the hook's
   stdin. Shape:
   ```json
   {
     "event": "Notification",
     "notification_type": "permission_prompt",
     "message": "<permission description string>",
     "cwd": "/path/to/project"
   }
   ```
2. Hook calls `read_event()` → parses the dict; outer guard catches any
   parse failure and calls `sys.exit(0)`.
3. Hook reads `notification_type` from the event. If not
   `permission_prompt` or `idle_prompt`, exit 0 silently.
4. **`permission_prompt` path:**
   a. Derive `project` name via `get_cwd().name`.
   b. Compute log path: `project_tmp_path("permission-log", project)` →
      `/tmp/zie-<project>-permission-log`.
   c. Read existing log file if it exists; parse as newline-delimited JSON
      records. If missing or unparseable, start with an empty list.
   d. Append a new record: `{"ts": "<ISO-8601 UTC>", "msg": "<message>"}`.
   e. Write updated log atomically via `safe_write_tmp`.
   f. Count records in the current session where `msg` matches the current
      `message` exactly (full string match).
   g. If count >= 3, print to stdout:
      ```json
      {"additionalContext": "This permission has been asked 3+ times this session. Run /zie-permissions to add it to the allow list."}
      ```
   h. Otherwise print nothing to stdout (no context injection).
5. **`idle_prompt` path:**
   a. Derive `project` name via `get_cwd().name`.
   b. Compute log path: `project_tmp_path("idle-log", project)` →
      `/tmp/zie-<project>-idle-log`.
   c. Append a newline-delimited JSON record:
      `{"ts": "<ISO-8601 UTC>", "msg": "<message>"}`.
   d. Write via `safe_write_tmp`.
   e. Print nothing to stdout.
6. Hook always exits 0. All inner I/O errors are caught and logged to
   stderr as `[zie-framework] notification-log: <error>`.

**hooks.json additions** (two new entries under `"Notification"`):
```json
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
```

Both entries point to the same script; the script branches internally on
`notification_type`.

**Output protocol for Notification hooks:** Return
`{"additionalContext": "..."}` JSON on stdout to inject context. Return
nothing (empty stdout) to pass through without injecting context.

---

**Edge Cases:**

- **Missing `notification_type` key** — outer guard treats as unknown type,
  exits 0 silently.
- **`message` key absent** — treat as empty string `""` for matching and
  logging; do not crash.
- **Log file is a symlink** — `safe_write_tmp` already refuses symlinks and
  returns False; hook logs a stderr warning and continues.
- **Log file is corrupted / not valid JSON lines** — catch parse error,
  reset to empty list, continue with fresh log for the session.
- **Concurrent hook invocations** (async: true means Claude may fire
  multiple events rapidly) — `safe_write_tmp` uses `os.replace()` for
  atomicity; last writer wins. Count may be off by one under extreme
  concurrency but this is acceptable for advisory-only context injection.
- **`get_cwd()` returns a path where `zie-framework/` does not exist** —
  hook still proceeds; the log is project-scoped by directory name
  regardless of whether zie-framework is initialized.
- **Very long `message` string** — no truncation; stored as-is. Log file
  stays in `/tmp` and is cleaned up by `session-cleanup.py` at Stop.
- **`permission_prompt` fires exactly 3 times with identical messages** —
  context is injected on the 3rd occurrence (count reaches 3, condition
  `>= 3` is true). On the 4th and subsequent it continues injecting.
- **`auth_success` / `elicitation_dialog` notification types** — not in
  scope; hook exits 0 on any unrecognized type.

---

**Out of Scope:**

- Auto-approving or blocking permissions (hook cannot return a block
  decision for Notification events; only `PreToolUse` with exit 2 can block).
- A `/zie-permissions` command implementation — that is a separate backlog
  item; this spec only advises the user to run it.
- Persisting permission logs across sessions (logs live in `/tmp` and are
  cleared by `session-cleanup.py` on Stop).
- UI or dashboard for permission analytics.
- `auth_success` and `elicitation_dialog` event handling.
- Deduplication across different sessions (session boundary = new `/tmp`
  file, since `session-cleanup.py` deletes tmp files on Stop).
