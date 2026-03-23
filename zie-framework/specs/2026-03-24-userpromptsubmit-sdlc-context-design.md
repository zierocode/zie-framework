---
approved: true
approved_at: 2026-03-24
backlog: backlog/userpromptsubmit-sdlc-context.md
---

# UserPromptSubmit SDLC Context Injection — Design Spec

**Problem:** Claude receives every user prompt without knowing the current SDLC
state, so it gives generic answers instead of stage-aware, task-specific guidance.

**Approach:** Add a new `hooks/sdlc-context.py` UserPromptSubmit hook that reads
`zie-framework/ROADMAP.md` (Now lane) and the last-test tmp file on every prompt,
then emits a structured `additionalContext` string so Claude always knows the
active task, current SDLC stage, suggested next command, and test status — with
no subprocess calls and guaranteed sub-100ms execution. The existing
`intent-detect.py` is kept intact; the two hooks compose by running sequentially
under the same UserPromptSubmit event, with `sdlc-context.py` injecting state
and `intent-detect.py` continuing to pattern-match and suggest commands.

**Components:**

- Create: `hooks/sdlc-context.py` — UserPromptSubmit hook; reads ROADMAP Now
  lane via `parse_roadmap_now`, reads last-test tmp file via `project_tmp_path`,
  derives stage name from Now-lane item text, and prints
  `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}, "additionalContext": "..."}` to stdout
- Modify: `hooks/hooks.json` — add a second entry inside the existing
  `UserPromptSubmit` hooks array so `sdlc-context.py` runs alongside
  `intent-detect.py` (no matcher needed)
- Create: `tests/test_sdlc_context.py` — unit tests covering: normal Now-lane
  output, empty Now lane, missing ROADMAP file, missing last-test tmp file,
  prompt > 500 chars (state still injected), concurrent-safe reads

**Data Flow:**

1. Claude Code fires `UserPromptSubmit`; stdin JSON contains `session_id`,
   `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `prompt`.
2. `read_event()` (utils) parses stdin; outer guard exits 0 on any parse failure.
3. `get_cwd()` resolves working directory; hook exits 0 if `zie-framework/`
   directory is absent (framework not initialized in this project).
4. `parse_roadmap_now(cwd / "zie-framework" / "ROADMAP.md")` returns a list of
   Now-lane items; if empty or file missing, `active_task = "none"` and
   `stage = "idle"`.
5. First Now-lane item is used as `active_task` (truncated to 80 chars to
   prevent context bloat). Stage name is derived by matching the item text
   against a keyword map: `spec` → `spec`, `plan` → `plan`, `implement`/`code`/
   `build` → `implement`, `fix`/`bug` → `fix`, `release`/`deploy` → `release`,
   `retro` → `retro`; unmatched → `in-progress`.
6. Suggested next command is looked up from a static stage → `/zie-*` map
   (same mapping as `intent-detect.py` `SUGGESTIONS`); `idle` stage maps to
   `/zie-status`.
7. Last-test tmp file is read via `project_tmp_path("last-test", cwd.name)`;
   if the file exists and its `st_mtime` is within the current session (compared
   against session start approximated by the `transcript_path` mtime), status is
   `"stale"` if mtime is > 300 s ago, else `"recent"`. If the tmp file is absent,
   status is `"unknown"`.
8. Hook prints:
   ```json
   {
     "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"},
     "additionalContext": "[sdlc] task: <active_task> | stage: <stage> | next: <suggested_cmd> | tests: <status>"
   }
   ```
9. On any inner exception (file I/O), error is logged to stderr and hook exits 0
   (Claude is never blocked).

**Edge Cases:**

- **Empty Now lane** — `active_task = "none"`, `stage = "idle"`,
  `suggested_cmd = "/zie-status"`; hook still emits context so Claude knows the
  project is idle.
- **Missing ROADMAP file** — `parse_roadmap_now` returns `[]`; handled
  identically to empty Now lane; no exception propagates.
- **Missing last-test tmp file** — `tests: unknown`; hook does not treat this as
  an error.
- **Prompt > 500 chars** — hook does not read or use the prompt at all; SDLC
  state is injected regardless of prompt length. (Prompt content is irrelevant
  to this hook's job; that concern belongs to `intent-detect.py`.)
- **Multiple concurrent prompts** — reads are read-only file ops; no write or
  lock is performed; concurrent execution is safe by construction.
- **`zie-framework/` absent** — hook exits 0 immediately; no output. Prevents
  noise in projects that do not use zie-framework.
- **Malformed or non-UTF-8 ROADMAP** — `parse_roadmap_now` raises; caught by
  inner exception handler; logs to stderr, exits 0.
- **Very long Now-lane item** — truncated to 80 chars before inclusion in
  `additionalContext` to bound output size.

**Out of Scope:**

- Replacing `intent-detect.py` entirely — that hook owns dangerous-pattern
  detection and prompt-to-command suggestions; it is not touched.
- Modifying the user's prompt text — `additionalContext` is appended metadata,
  not a prompt rewrite; `updatedPrompt` is never emitted.
- Reading git branch or running `git` subprocess — would risk exceeding 100ms
  budget and violates the no-subprocess rule; git state is not included.
- Reading test results content (stdout/stderr) — only the mtime of the
  last-test tmp file is read; parsing test output is out of scope.
- Per-project stage configuration — stage-to-command mapping is a fixed static
  table in this hook; runtime overrides via `.config` are not included.
- Persisting context to zie-memory — this hook is read-only and stateless;
  memory integration belongs to `wip-checkpoint.py`.
