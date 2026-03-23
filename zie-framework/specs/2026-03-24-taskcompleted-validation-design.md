---
approved: true
approved_at: 2026-03-24
backlog: backlog/taskcompleted-validation.md
---

# TaskCompleted Quality Gate Hook — Design Spec

**Problem:** When Claude marks a Task as completed via `TaskUpdate status=completed`, there is no gate to verify that tests are passing or that implementation files are committed, so tasks get marked done in a broken state.

**Approach:** A new `TaskCompleted` hook (`hooks/task-completed-gate.py`) intercepts the completion event before it is applied and returns exit code 2 with a specific failure reason on stderr if checks fail, which causes Claude Code to treat the block message as a reason to continue working rather than completing the task. The gate is selective — it only enforces for tasks whose subject contains `implement` or `fix` (case-insensitive); all other tasks (docs, plans, specs) are allowed through unconditionally. Checks are cache-inspection-only (no subprocess test run) to stay under the 2-second budget.

**Components:**
- `hooks/task-completed-gate.py` — new hook (primary deliverable)
- `hooks/hooks.json` — add `TaskCompleted` event entry pointing to the new hook
- `tests/test_task_completed_gate.py` — new unit test file
- `hooks/utils.py` — no changes required; `read_event()` and `get_cwd()` are reused as-is

---

## Data Flow

1. Claude calls `TaskUpdate` with `status=completed` and a task subject string.
2. Claude Code fires the `TaskCompleted` hook, passing a JSON event on stdin with shape:
   ```json
   {
     "tool_name": "TaskUpdate",
     "tool_input": {
       "id": "<task-id>",
       "status": "completed",
       "title": "<task subject>"
     }
   }
   ```
3. Hook reads the event via `read_event()` (outer guard — any parse failure → `sys.exit(0)`).
4. Extract `title` from `tool_input`. If absent or empty → `sys.exit(0)`.
5. **Advisory-mode check:** Lowercase the title. If neither `implement` nor `fix` appears in it → print `[zie-framework] task-completed-gate: advisory task — gate skipped` to stdout and `sys.exit(0)`.
6. Resolve `cwd` via `get_cwd()`.
7. **Check 1 — pytest last-failed cache:**
   - Inspect `<cwd>/.pytest_cache/v/cache/lastfailed` (JSON file).
   - If file exists and its parsed content is a non-empty dict → gate blocks:
     ```
     stderr: [zie-framework] BLOCKED: tests are failing — fix failures before marking done.
             Failed: <comma-separated keys from lastfailed dict, max 5>
     exit(2)
     ```
   - If file is missing, empty, or contains `{}` → check passes (tests are clean or never run).
   - On any `OSError` or `json.JSONDecodeError` → skip this check silently, continue to Check 2.
8. **Check 2 — uncommitted implementation files:**
   - Run `git -C <cwd> status --short` via `subprocess.run` with `timeout=5`, `capture_output=True`.
   - Filter stdout lines to those matching implementation file extensions: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`, `.rb`, `.java`, `.kt`, `.swift`, `.c`, `.cpp`, `.h`.
   - Exclude lines matching test-file indicators: `test_`, `_test.`, `.test.`, `.spec.`.
   - If any matching lines remain → gate warns (non-blocking):
     ```
     stdout: [zie-framework] WARNING: uncommitted implementation files detected — consider committing before closing task.
             <file list, max 5 lines>
     exit(0)  # warn only — does not block
     ```
   - On `subprocess.TimeoutExpired`, `FileNotFoundError` (git not installed), or any other exception → skip silently, `sys.exit(0)`.
9. All checks passed → `sys.exit(0)` (no output needed).

---

## Hook Registration

Add to `hooks/hooks.json` under the top-level `"hooks"` object:

```json
"TaskCompleted": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/task-completed-gate.py\""
      }
    ]
  }
]
```

Also add `"TaskCompleted"` to the `_hook_output_protocol` annotation dict with value:
`"exit(2) + stderr message to block; stdout warning for non-blocking notices"`.

---

## Edge Cases

- **No `.pytest_cache` directory** (project never ran pytest, or uses a different test runner): `lastfailed` file will not exist → check passes cleanly.
- **`lastfailed` contains `{}`** (last run had no failures): treat as passing — this is pytest's own "clean" sentinel value.
- **Task title is None or missing from event payload**: outer guard catches this, `sys.exit(0)`.
- **`git` binary not on PATH**: `FileNotFoundError` caught in inner except — hook exits 0, Claude is never blocked.
- **`cwd` is not a git repo**: `git status` returns non-zero; stdout will be empty or contain an error line with no matching extensions — no false-positive block.
- **Large `lastfailed` dict**: only show first 5 keys in stderr output to keep feedback readable.
- **Hook runs in a project with no `zie-framework/` directory**: hook still operates — it does not require zie-framework to be self-hosted. `get_cwd()` is sufficient.
- **Concurrent hook invocations**: all operations are read-only (cache inspection + git status); no write contention possible.
- **`TaskUpdate` called with `status` other than `completed`**: the event still fires `TaskCompleted` only on completion; no extra status filter needed in the hook body (the event type itself is the filter).
- **Two-tier error handling per ADR-003**: outer `try/except Exception` wraps the entire `main()` body with `sys.exit(0)` fallback; inner operations use `except Exception as e: print(..., file=sys.stderr)` and continue, never raising unhandled exceptions, never exiting non-zero on unexpected errors.

---

## Out of Scope

- Running the full test suite (`make test` or `pytest` subprocess) — cache inspection only, no live test execution.
- Checking test coverage thresholds.
- Validating that acceptance criteria in the task description were addressed (natural-language parsing).
- Blocking on uncommitted docs, spec, or plan files — only implementation file extensions are checked.
- Reporting on tasks that were never tested at all (no `.pytest_cache` present is treated as passing, not an error).
- Integration with zie-memory or any external API.
- Support for non-pytest test runners in Check 1 (vitest/jest do not use `.pytest_cache`; Check 1 is silently skipped when the file is absent).
