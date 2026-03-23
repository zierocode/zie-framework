---
approved: true
approved_at: 2026-03-24
backlog: backlog/configchange-drift-detection.md
---

# ConfigChange CLAUDE.md Drift Detection — Design Spec

**Problem:** When `CLAUDE.md` or `.claude/settings.json` changes on disk during
an active session (via another terminal, `git pull`, or `/zie-resync`), Claude
Code continues operating on the stale instructions it loaded at session start.

**Approach:** A new `hooks/config-drift.py` hook registers on the `ConfigChange`
event with matcher `project_settings|user_settings`. On each event it inspects
the `file_path` field of the payload, classifies the changed file as
`CLAUDE.md`, `settings.json`, or a `zie-framework/.config` change, and emits an
`additionalContext` JSON payload instructing Claude to re-read the affected file
before continuing. If the changed file is unrecognised (not in the watch list)
the hook exits silently. Because `ConfigChange` outputs `additionalContext`, the
hook follows the `UserPromptSubmit` output protocol: JSON
`{"additionalContext": "..."}` printed to stdout.

**Components:**

- `hooks/config-drift.py` — new hook (primary deliverable)
- `hooks/hooks.json` — add a new `ConfigChange` top-level event entry with
  matcher `project_settings|user_settings` pointing to `config-drift.py`
- `hooks/utils.py` — no changes needed; `read_event()` and `get_cwd()` reused
  as-is
- `tests/test_config_drift.py` — new unit test module
- `zie-framework/project/components.md` — add `config-drift.py` row to Hooks
  table

**Data Flow:**

1. A file under `.claude/` (or the project root `CLAUDE.md`) changes on disk;
   Claude Code fires the `ConfigChange` event.
2. Claude Code invokes `config-drift.py` with the event JSON on stdin. The event
   payload shape is:
   ```json
   {
     "hook_event_name": "ConfigChange",
     "file_path": "/abs/path/to/changed/file"
   }
   ```
3. **Outer guard** — `read_event()` parses stdin. On any parse failure or if
   `hook_event_name` is not `"ConfigChange"`, call `sys.exit(0)` immediately
   (ADR-003).
4. Extract `file_path = event.get("file_path", "")`. If empty, `sys.exit(0)`.
5. Resolve `cwd = get_cwd()`. Compute `Path(file_path)` as `changed`.
6. **Classification** — check `changed` against three patterns in order:

   a. **CLAUDE.md** — `changed.name == "CLAUDE.md"`. This covers both the
      project-root `CLAUDE.md` and any nested variant.

   b. **settings.json** — `changed.name == "settings.json"` and `".claude"` is
      anywhere in `changed.parts`.

   c. **zie-framework/.config** — `changed.name == ".config"` and the path is
      under `cwd / "zie-framework"`.

   If none match, `sys.exit(0)` — unrelated config change, stay quiet.

7. **Inner operations** — build the `additionalContext` string based on which
   class matched:

   - **CLAUDE.md** →
     `"[zie-framework] CLAUDE.md has been updated on disk. Re-read it now with Read('{file_path}') before continuing so your instructions are current."`

   - **settings.json** →
     `"[zie-framework] .claude/settings.json has been updated on disk. Re-read it now with Read('{file_path}') before continuing so your permission rules are current."`

   - **zie-framework/.config** →
     `"[zie-framework] zie-framework/.config has changed. Run /zie-resync to reload project configuration before continuing."`

8. Print `json.dumps({"additionalContext": msg})` to stdout and `sys.exit(0)`.
   Claude Code injects the string into the next context window; Claude re-reads
   the file (or runs `/zie-resync`) before responding.

**Edge Cases:**

- `file_path` absent or empty in event payload — `sys.exit(0)`; no output.
  Prevents `KeyError` or empty-string path resolution.
- `file_path` is a relative path — `Path(file_path)` still resolves; `.name`
  and `.parts` checks are path-segment comparisons that work on relative paths.
  No `cwd`-join needed for the CLAUDE.md and settings.json cases since they
  match on name only.
- `file_path` refers to a file that no longer exists (deleted, not modified) —
  the hook only reads the path string, never opens the file; classification and
  context injection work regardless.
- Both `CLAUDE.md` and `settings.json` change simultaneously — `ConfigChange`
  fires once per changed file; each invocation is independent; both will
  individually emit their context strings. No deduplication needed.
- `zie-framework/` directory does not exist in `cwd` (project not initialised
  with zie-framework) — the `zie-framework/.config` branch can never match;
  CLAUDE.md and settings.json branches still function normally since they do not
  require `zie-framework` to be present.
- Hook runs outside a zie-framework project (no `zie-framework/` dir) — no
  guard on this by design. `CLAUDE.md` drift detection is useful even before
  `/zie-init` has run, since CLAUDE.md is the root instruction file.
- `CLAUDE_CWD` env var unset — `get_cwd()` falls back to `os.getcwd()`;
  `.config` path comparison may be less reliable in edge cases, but CLAUDE.md
  and settings.json detection are unaffected.
- Symlinked `CLAUDE.md` or `settings.json` — `Path.name` operates on the
  symlink path, not the target; classification still matches correctly; no
  symlink-following needed.
- Malformed `file_path` (control characters, null bytes) — `Path()` constructor
  raises `ValueError` on null bytes; catch in the outer `except Exception` guard
  and `sys.exit(0)`.
- Hook invoked for a `ConfigChange` event variant not yet in the Claude Code
  spec — unrecognised `file_path` values fall through all three classification
  branches and exit silently; no noise emitted.

**Out of Scope:**

- Hash-based deduplication to suppress re-notification when a file is saved
  without content changes — Claude Code fires `ConfigChange` only on actual
  content writes; assumed non-issue at this layer.
- Automatically re-reading the file on behalf of Claude (i.e., the hook calling
  `Read` itself) — hooks cannot invoke Claude tools; `additionalContext`
  instructs Claude to do it.
- Watching arbitrary project files beyond `CLAUDE.md`, `settings.json`, and
  `zie-framework/.config` — scope is limited to the three files identified in
  the backlog.
- Diffing old vs. new file content to summarise what changed — hook has no
  access to pre-change content; summary is Claude's responsibility after re-read.
- Rate-limiting or debouncing repeated `ConfigChange` events in rapid succession
  (e.g., editor auto-save loops) — each event is handled independently; Claude
  receives multiple context injections but this is acceptable given the
  low-frequency nature of config changes.
- Blocking the turn (`decision: block`) on config drift — notification via
  `additionalContext` is sufficient; hard-blocking would interrupt work in
  progress and is disproportionate.
- Per-project opt-out via `.config` flag — not implemented in this iteration.
