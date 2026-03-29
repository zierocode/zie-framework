---
approved: true
approved_at: 2026-03-24
backlog: backlog/subagent-lifecycle-hooks.md
---

# SubagentStop Capture + Resume Subagent Pattern — Design Spec

**Problem:** When reviewer subagents finish, their findings and identity are lost — there is no record of which agents ran, what they last said, or how to resume one for a follow-up question.

**Approach:** Add a new `SubagentStop` hook (`hooks/subagent-stop.py`) registered as `async: true` (non-blocking) that appends a JSONL entry per completed subagent to a project-scoped `/tmp` log. `/zie-retro` reads this log to surface a "agents used this session" summary. The resume pattern (referencing an agent by ID via `@agent:<id>`) is documented inside `/zie-implement` so reviewers can be continued without a cold context reload.

**Components:**
- `hooks/subagent-stop.py` — new hook (SubagentStop event)
- `hooks/hooks.json` — new `SubagentStop` entry with `async: true`
- `hooks/utils.py` — `project_tmp_path` and `get_cwd` already support this; no changes required
- `commands/zie-retro.md` — add "Subagent Activity" section that reads the JSONL log
- `commands/zie-implement.md` — add resume-subagent documentation block

---

## Data Flow

1. A subagent (spec-reviewer, plan-reviewer, impl-reviewer, or any other) completes its turn.
2. Claude Code fires the `SubagentStop` event and writes a JSON payload to the hook's stdin. Payload shape (as documented in Claude Code hook protocol):
   ```json
   {
     "agent_id": "<uuid>",
     "agent_type": "<string>",
     "last_assistant_message": "<string>"
   }
   ```
3. `subagent-stop.py` outer guard: `read_event()` parses stdin → if parse fails, `sys.exit(0)`.
4. Outer guard: `get_cwd()` → check `zie-framework/` subdir exists → if not, `sys.exit(0)` (not a zie project).
5. Inner operation: build log path via `project_tmp_path("subagent-log", cwd.name)` → resolves to `/tmp/zie-<safe_project>-subagent-log`.
6. Inner operation: build JSONL record:
   ```json
   {"ts": "<ISO-8601 UTC>", "agent_id": "<id>", "agent_type": "<type>", "last_message": "<truncated to 500 chars>"}
   ```
   `last_message` is truncated at 500 characters to keep the log file bounded; full output is available in the agent's own turn transcript.
7. Inner operation: open log file in append mode (`"a"`) and write the JSON line + `\n`. No atomic rename needed — append is used because this is a cumulative log (not a single-owner file), and JSONL append is safe for this use case (single-writer: only this hook writes to it).
8. Hook exits 0. Because `async: true`, Claude is never blocked.
9. At retro time, `/zie-retro` reads the JSONL file line-by-line, parses each record, and prints a summary table: agent type, agent ID (truncated), and a snippet of the last message.
10. At session end, `session-cleanup.py` (existing) removes the log via its `glob(f"zie-{safe_project}-*")` sweep — no changes needed there.

---

## Edge Cases

- **`SubagentStop` payload missing fields** — access via `event.get("agent_id", "unknown")` etc. for all three fields; never use bare key access. A record with `"unknown"` values is still written (provides a signal that an agent ran even if metadata is incomplete).
- **`/tmp` not writable** — the `except Exception as e: print(...)` inner guard catches `OSError`; hook exits 0.
- **Log file does not exist yet** — open with `"a"` creates the file; `Path.parent` is `/tmp` which always exists.
- **Log file is a symlink** — check `os.path.islink(log_path)` before opening; if True, log warning to stderr and skip write (mirrors `safe_write_tmp` pattern in utils.py).
- **`last_assistant_message` is None or non-string** — coerce with `str(event.get("last_assistant_message") or "")` before truncation.
- **Very large `last_assistant_message`** — cap at 500 chars before writing; prevents unbounded log growth in sessions with many agents.
- **`zie-framework/` absent** — outer guard exits early; hook is a no-op on non-zie projects.
- **`/zie-retro` run with no log file** — retro reads the path, catches `FileNotFoundError`, prints "No subagent activity recorded this session." and continues normally.
- **Multiple agents of same type in one session** — each gets its own JSONL line; retro groups by `agent_type` when displaying the summary.
- **Resume pattern: agent ID no longer valid** — document in `/zie-implement` that agent IDs are session-scoped; if the session has ended, a fresh subagent must be started.

---

## Out of Scope

- Persisting the subagent log beyond the current session (it lives in `/tmp` and is cleaned by `session-cleanup.py`).
- Storing subagent findings in zie-memory — that is retro's responsibility via existing `remember` calls.
- Streaming or real-time display of subagent activity during a session.
- Filtering or routing by `agent_type` at hook time — all subagents are logged uniformly; filtering is the consumer's (retro's) job.
- Modifying the Claude Code agent-spawning behavior — this spec only observes completions, it does not control scheduling.
- A UI or dashboard for subagent activity — retro summary is plain text only.
- Changes to `session-cleanup.py` — existing glob pattern already covers the new log file name.

---

## Hook Registration (hooks.json addition)

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

`async: true` is required — SubagentStop fires frequently during complex pipelines and must never add latency to the main agent turn.

---

## Test Cases

1. **Normal write** — valid event with all fields → JSONL line appended to correct path, fields match, `last_message` truncated at 500 chars.
2. **Missing fields** — event with empty dict `{}` → line written with `"unknown"` values, no exception raised.
3. **`last_assistant_message` is None** → coerced to `""`, line written cleanly.
4. **Long message** — message of 1000 chars → stored as 500 chars exactly.
5. **Non-zie project** (no `zie-framework/` dir) → nothing written, exits 0.
6. **Symlink guard** — log path is a symlink → write skipped, warning on stderr, exits 0.
7. **Malformed stdin** — `read_event()` returns `{}` on parse failure → outer guard `sys.exit(0)`, no crash.
8. **Multiple calls in sequence** — three events → three JSONL lines in order, file readable line-by-line.
9. **Retro with existing log** — log with two agent types → retro summary table shows both, grouped correctly.
10. **Retro with no log file** — `FileNotFoundError` → "No subagent activity recorded this session." printed, retro continues.
