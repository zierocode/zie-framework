---
approved: true
approved_at: 2026-03-24
backlog: backlog/stopfailure-logging.md
---

# StopFailure API Error Logging — Design Spec

**Problem:** When Claude Code's API fails mid-session (rate limit, billing error, server error), the session silently terminates with no record of what was in progress or why it stopped.

**Approach:** A new `StopFailure` hook script (`hooks/stopfailure-log.py`) intercepts API failure events and appends a structured log entry to a project-scoped file under `/tmp`. The log captures timestamp, error type, error details, and the current ROADMAP Now lane so context is preserved for the next session. For user-actionable errors (`rate_limit`, `billing_error`), the hook also writes a human-readable message to stderr, which Claude Code surfaces as a visible notification.

**Components:**
- `hooks/stopfailure-log.py` — new hook (StopFailure event handler)
- `hooks/hooks.json` — add `StopFailure` entry registering the new script with `async: true`
- `hooks/utils.py` — no changes; reuses `project_tmp_path`, `safe_project_name`, `read_event`, `get_cwd`, `parse_roadmap_now`, `safe_write_tmp`
- `tests/test_stopfailure_log.py` — new test file

---

## Data Flow

1. Claude Code fires `StopFailure` event; hook receives JSON payload on stdin.
2. `read_event()` parses stdin → `event` dict. On parse failure → `sys.exit(0)`.
3. Extract fields from `event`:
   - `event.get("error_type", "unknown")` — e.g. `"rate_limit"`, `"billing_error"`, `"api_error"`, `"overloaded_error"`
   - `event.get("error_details", "")` — optional detail string
   - `event.get("last_assistant_message", "")` — last message before failure (unused in log body but available for future use)
4. `get_cwd()` → `cwd`; guard: if `(cwd / "zie-framework")` does not exist → `sys.exit(0)` (not a zie-framework project).
5. `parse_roadmap_now(cwd / "zie-framework" / "ROADMAP.md")` → `wip_lines`; join first 3 items as `wip_summary` (empty string if ROADMAP absent).
6. Build log entry string:
   ```
   [<ISO-8601 UTC timestamp>] error_type=<type> wip=<wip_summary> details=<error_details>
   ```
7. Compute log path: `project_tmp_path("failure-log", safe_project_name(cwd.name))` → `/tmp/zie-<project>-failure-log`.
8. Append log entry to the file (open in `"a"` mode, write line + newline). Wrap in `try/except Exception as e` → print to stderr, then `sys.exit(0)`.
9. If `error_type in {"rate_limit", "billing_error"}`: print a human-readable message to stderr:
   ```
   [zie-framework] Session stopped: <error_type>. Wait before resuming.
   ```
   All other error types: silent (no stderr output).
10. `sys.exit(0)` — hook always exits cleanly.

---

## Edge Cases

- **Malformed / missing event JSON:** `read_event()` exits 0 before any logic runs.
- **Not a zie-framework project (no `zie-framework/` dir):** early exit at step 4; no file written.
- **ROADMAP.md absent or Now section empty:** `parse_roadmap_now` returns `[]`; `wip_summary` is `""`.
- **`/tmp` write failure (permissions, disk full):** caught by inner `try/except`; error printed to stderr; hook still exits 0.
- **`error_type` not in known set:** treated as silent log-only (no stderr notification).
- **`error_details` absent in payload:** defaults to `""` — log entry still written.
- **Concurrent sessions writing to same failure-log:** append mode (`"a"`) is safe for single-writer-per-project scenarios; log entries may interleave across concurrent sessions but remain parseable per-line.
- **`session-cleanup.py` deletes the failure-log on normal Stop:** this is correct and by design — the log is ephemeral `/tmp` state. The StopFailure hook only fires on API errors, not on normal Stop, so cleanup does not race with logging.

---

## Hook Registration (`hooks/hooks.json`)

Add a new top-level `StopFailure` event block alongside the existing `Stop` block:

```json
"StopFailure": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stopfailure-log.py\""
      }
    ]
  }
]
```

Note: Claude Code does not expose an `async` field in hook registration JSON (based on current hooks.json schema — no existing hook uses it). The `async: true` intent from the backlog is satisfied by the hook's guaranteed `sys.exit(0)` path — it never blocks Claude regardless of I/O speed.

---

## Test Cases (`tests/test_stopfailure_log.py`)

1. **`test_log_written_rate_limit`** — rate_limit event → log file created, entry contains `error_type=rate_limit`, stderr contains notification message.
2. **`test_log_written_billing_error`** — billing_error event → log file created, stderr contains notification message.
3. **`test_log_written_api_error_silent`** — api_error event → log file created, stderr is empty (no notification).
4. **`test_log_written_overloaded_error_silent`** — overloaded_error event → log file created, stderr is empty.
5. **`test_log_written_unknown_error_silent`** — unknown/arbitrary error type → log file created, stderr is empty.
6. **`test_wip_in_log_entry`** — event with readable ROADMAP fixture → log entry contains the Now lane WIP items.
7. **`test_no_zie_framework_dir_exits_clean`** — cwd with no `zie-framework/` subdir → no log file written, exit 0.
8. **`test_malformed_stdin_exits_clean`** — invalid JSON on stdin → no log file written, exit 0.
9. **`test_log_appends_on_multiple_calls`** — hook invoked twice → log file has two lines.
10. **`test_no_crash_on_tmp_write_failure`** — mock open to raise OSError → no exception propagates, exit 0.

---

## Out of Scope

- Persisting the failure log beyond the session (the file lives in `/tmp` and is cleaned up by `session-cleanup.py` on the next normal Stop).
- Sending failure data to zie-memory API (no API endpoint exists for this event type).
- Structured JSON log format (plain-text append is sufficient for the audit trail use case).
- Desktop OS-level notifications (stderr output is the notification mechanism Claude Code provides).
- Retry or recovery logic — this hook is observability only.
- Parsing or acting on `last_assistant_message` content.
