---
approved: true
approved_at: 2026-03-24
backlog: backlog/prepostcompact-wip-preservation.md
---

# PreCompact/PostCompact WIP Preservation — Design Spec

**Problem:** When Claude Code compacts context, all active SDLC state (current task, TDD phase, recently modified files) is lost and must be re-discovered from scratch, wasting turns and causing mistakes.

**Approach:** A single new hook script `hooks/sdlc-compact.py` handles both PreCompact and PostCompact events. On PreCompact it writes a JSON snapshot of live SDLC state to a project-scoped `/tmp` path via `safe_write_tmp()`. On PostCompact it reads that snapshot and emits it as `hookSpecificOutput.additionalContext` so Claude receives full SDLC continuity immediately after compaction.

**Components:**
- Create: `hooks/sdlc-compact.py` — dual-event hook; branches on `event["hook_event_name"]`; PreCompact path collects and persists state snapshot; PostCompact path reads snapshot and prints JSON context to stdout
- Modify: `hooks/hooks.json` — register `sdlc-compact.py` for both `PreCompact` and `PostCompact` events
- Create: `tests/test_sdlc_compact.py` — unit tests: snapshot roundtrip, missing snapshot on PostCompact, empty ROADMAP, non-project CWD

**Data Flow:**

PreCompact path:
1. Claude Code fires `PreCompact`; stdin delivers `{"hook_event_name": "PreCompact", "cwd": "<path>", ...}`
2. `read_event()` parses stdin → `event` dict; outer guard checks `hook_event_name == "PreCompact"`; if not a zie-framework project (`cwd / "zie-framework"` absent), `sys.exit(0)`
3. `get_cwd()` resolves `CLAUDE_CWD` env var → `cwd`; `project_name = cwd.name`
4. `parse_roadmap_now(cwd / "zie-framework" / "ROADMAP.md")` → `now_items` list (first item is active task)
5. `subprocess.run(["git", "-C", str(cwd), "branch", "--show-current"])` → `git_branch` string; captured with `capture_output=True, text=True`; falls back to `""` on any exception
6. `subprocess.run(["git", "-C", str(cwd), "diff", "--name-only", "HEAD"])` → `changed_files` list (split on newlines); falls back to `[]` on any exception
7. Read `cwd / "zie-framework" / ".config"` → parse `tdd_phase` field (default `""`); ignore parse errors
8. Build snapshot dict: `{"active_task": now_items[0] if now_items else "", "git_branch": git_branch, "changed_files": changed_files[:20], "tdd_phase": tdd_phase, "now_items": now_items}`
9. `safe_write_tmp(project_tmp_path("compact-snapshot", project_name), json.dumps(snapshot))` → writes atomically to `/tmp/zie-<safe-project-name>-compact-snapshot`
10. Hook exits 0; no stdout output required for PreCompact

PostCompact path:
1. Claude Code fires `PostCompact`; stdin delivers `{"hook_event_name": "PostCompact", "cwd": "<path>", ...}`
2. `read_event()` parses stdin → `event` dict; outer guard checks `hook_event_name == "PostCompact"`; if not a zie-framework project, `sys.exit(0)`
3. `get_cwd()` → `cwd`; `project_name = cwd.name`
4. Read `project_tmp_path("compact-snapshot", project_name)` → parse JSON into `snapshot`; if file missing or parse fails, emit minimal fallback context (active task from live ROADMAP only) and exit 0
5. Build human-readable context block from snapshot fields: active task, TDD phase, git branch, changed files list
6. Print to stdout: `json.dumps({"hookSpecificOutput": {"additionalContext": "<context block>"}})` — Claude Code injects this into the refreshed context window

**Edge Cases:**
- Missing snapshot file on PostCompact: snapshot file absent (e.g., first compact, or `/tmp` cleared) — PostCompact reads live ROADMAP as fallback and emits whatever `now_items` returns; never errors or blocks
- Empty ROADMAP / missing Now section: `parse_roadmap_now()` returns `[]`; `active_task` is `""`; snapshot is written with empty string; PostCompact context block omits the active task line rather than emitting a blank line
- Non-project CWD (no `zie-framework/` dir): both PreCompact and PostCompact guard exit 0 immediately after CWD check; no file I/O attempted
- Concurrent hook invocations: `safe_write_tmp()` uses `os.replace()` (atomic on POSIX) so a concurrent PreCompact write will not produce a torn file; PostCompact that races a PreCompact write will read either the previous complete snapshot or the new one — both are valid
- Snapshot path is a symlink: `safe_write_tmp()` detects `os.path.islink()` and returns `False`; hook logs a stderr warning and exits 0; Claude is not blocked
- `git` not available or cwd is not a git repo: `subprocess.run` call is wrapped in try/except; `git_branch` defaults to `""` and `changed_files` defaults to `[]`; snapshot is still written with remaining fields intact

**Out of Scope:**
- Persisting snapshot across machine reboots or `/tmp` clears (tmp-only by design)
- Diffing or merging multiple snapshots from nested compactions
- Tracking TDD phase transitions within the hook (reads `.config` as written by other commands)
- Compacting or truncating the `changed_files` list beyond the 20-item cap
- Notifying zie-memory on compact (handled by existing `wip-checkpoint.py`)
