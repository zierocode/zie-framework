---
approved: true
approved_at: 2026-03-24
backlog: backlog/posttoolusefailure-debug-context.md
---

# PostToolUseFailure Debugging Context Injection — Design Spec

**Problem:** When a Bash, Write, or Edit tool call fails, Claude has no SDLC
context at the point of failure and must investigate from scratch, burning extra
turns to diagnose the issue.

**Approach:** A new `PostToolUseFailure` hook (`hooks/failure-context.py`)
intercepts failures on `Bash|Write|Edit` tool calls and injects an
`additionalContext` JSON payload containing the active ROADMAP Now-lane task,
the last git commit, the current branch, and a quick-fix hint. When
`is_interrupt: true` is present the hook exits early with no output, since the
failure was user-initiated rather than a real error. All output follows the
`PostToolUseFailure` protocol: a single JSON object `{"additionalContext": "..."}`
printed to stdout.

**Components:**

- `hooks/failure-context.py` — new hook (primary deliverable)
- `hooks/hooks.json` — add `PostToolUseFailure` entry with matcher
  `Bash|Write|Edit`
- `hooks/utils.py` — reuse `read_event()`, `get_cwd()`,
  `parse_roadmap_now()` (no changes needed)
- `tests/test_failure_context.py` — new unit test module
- `zie-framework/project/components.md` — add hook row to Hooks table

---

## Data Flow

1. Claude Code fires `PostToolUseFailure` event; hook process receives event
   JSON on stdin.
2. `read_event()` parses the JSON into a dict. Any parse failure → `sys.exit(0)`.
3. **Outer guard** — check `event.get("is_interrupt", False)`. If `True`,
   `sys.exit(0)` immediately (user cancelled; no debug context needed).
4. **Tool filter** — check `event.get("tool_name", "")` is in
   `{"Bash", "Write", "Edit"}`. If not, `sys.exit(0)`.
5. `get_cwd()` resolves the project root.
6. **ROADMAP read** — locate `zie-framework/ROADMAP.md` relative to cwd.
   Call `parse_roadmap_now(roadmap_path)` → `now_items: list[str]`.
   If file missing or section empty, `now_items = []`.
7. **Git context** — run `subprocess.run(["git", "log", "-1", "--pretty=%h %s"],
   capture_output=True, text=True, cwd=str(cwd), timeout=5)`. On any exception
   or non-zero returncode, set `last_commit = "(git unavailable)"`.
   Run `subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], ...)` for
   branch name; default to `"(unknown)"` on failure.
8. **Build context string** — compose a multi-line string:

   ```
   [SDLC context at failure]
   Active task: <now_items[0] or "(none — check ROADMAP Now lane)">
   Branch: <branch>
   Last commit: <last_commit>
   Quick fix: run `make test-unit` to reproduce; check output above for root cause.
   ```

9. Print `json.dumps({"additionalContext": context_string})` to stdout.
10. `sys.exit(0)` always — hook never blocks Claude.

---

## Edge Cases

- **`is_interrupt: true`** — exit 0, emit nothing. User intentionally cancelled;
  injecting debug context would be noise.
- **ROADMAP.md missing** — `parse_roadmap_now()` already returns `[]`; render
  active task as `"(none — check ROADMAP Now lane)"`.
- **ROADMAP Now lane empty** — same fallback as above.
- **git not installed / not a git repo** — subprocess raises `FileNotFoundError`
  or returns non-zero; catch and use `"(git unavailable)"` for both fields.
- **git subprocess timeout** (5 s) — catch `subprocess.TimeoutExpired`; use
  fallback strings.
- **event has no `tool_name`** — `event.get("tool_name", "")` returns `""`; not
  in the allowed set → `sys.exit(0)`.
- **cwd has no `zie-framework/` subdirectory** — ROADMAP path does not exist;
  `parse_roadmap_now()` handles gracefully; git context still collected from cwd.
- **stdout write failure** — wrapped in inner try/except; log to stderr, exit 0.
- **Concurrent hook execution** — hook is read-only (no tmp files written), so
  no race condition.

---

## Output Protocol

`PostToolUseFailure` is not yet documented in `hooks.json`'s
`_hook_output_protocol` comment block. The implementation must emit:

```json
{"additionalContext": "<string>"}
```

This matches the `UserPromptSubmit` convention (the only other event that uses
`additionalContext`). The `_hook_output_protocol` comment in `hooks.json` must
be updated to add:

```
"PostToolUseFailure": "JSON {\"additionalContext\": \"...\"} printed to stdout"
```

---

## Hook Registration (`hooks/hooks.json`)

Add inside the top-level `"hooks"` object:

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

---

## Test Cases (`tests/test_failure_context.py`)

All tests use `subprocess.run` or direct function-level imports with monkeypatching.

| # | Scenario | Input | Expected stdout |
|---|---|---|---|
| 1 | Normal failure, ROADMAP has Now item | tool=Bash, is_interrupt absent, ROADMAP with active task | `additionalContext` contains task name, branch, commit |
| 2 | `is_interrupt: true` | tool=Bash, is_interrupt=true | empty stdout (exit 0) |
| 3 | ROADMAP missing | tool=Edit, no ROADMAP file | `additionalContext` contains `"(none — check ROADMAP Now lane)"` |
| 4 | ROADMAP Now lane empty | tool=Write, Now section has no items | same fallback as above |
| 5 | Tool not in matcher set | tool=Read | empty stdout (exit 0) |
| 6 | git unavailable | mock subprocess to raise FileNotFoundError | `additionalContext` contains `"(git unavailable)"` |
| 7 | JSON output is valid | any passing case | `json.loads(stdout)` succeeds; key is `"additionalContext"` |

---

## Out of Scope

- Injecting context for tool events other than `Bash`, `Write`, `Edit`.
- Storing failure events to zie-memory or any persistent log.
- Diff output or full git log history (last commit summary only).
- Retry logic or auto-fix suggestions beyond the `make test-unit` hint.
- Customising the hint string via `.config` (can be a future backlog item).
- Changes to any existing hook behaviour.
