---
approved: true
approved_at: 2026-03-24
backlog: backlog/plugin-settings-defaults.md
---

# Plugin settings.json Defaults + CLAUDE_PLUGIN_DATA Storage — Design Spec

**Problem:** zie-framework ships no `settings.json` and writes all hook state to
`/tmp`, so accumulated data (review pattern cache, subagent log archive, WIP edit
counters) is silently discarded at each session restart.

**Approach:** Add a `settings.json` at the plugin root (`.claude-plugin/`) with
the `agent:` key populated once a default agent is defined, and add a
`safe_write_persistent()` utility to `hooks/utils.py` that resolves
`$CLAUDE_PLUGIN_DATA` at call time with graceful fallback to `/tmp`. Migrate the
two hooks whose state benefits from persistence (`wip-checkpoint` edit counter
and `session-learn` pending-learn marker) to use the persistent path, while
leaving pure session-scoped state (debounce timestamps in `auto-test`) on `/tmp`.
The distinction is documented via a new docstring convention in `utils.py`.

**Components:**
- `.claude-plugin/settings.json` — new file; plugin-level defaults (`agent:` key,
  left empty until a default agent command is defined)
- `hooks/utils.py` — add `get_plugin_data_dir()` and `safe_write_persistent()`
  functions; add module-level docstring clarifying `/tmp` vs persistent storage
- `hooks/wip-checkpoint.py` — migrate edit counter file from
  `project_tmp_path("edit-count", …)` to `persistent_project_path("edit-count", …)`
- `hooks/session-learn.py` — migrate `pending_learn.txt` from
  `~/.claude/projects/<project>/pending_learn.txt` to the persistent dir
  (simplifies path construction; no more manual `.claude/projects/` resolution)
- `hooks/session-cleanup.py` — scope cleanup to `/tmp` only; must NOT delete
  files under `CLAUDE_PLUGIN_DATA`
- `tests/test_utils.py` — new or extended test cases for `get_plugin_data_dir()`
  and `safe_write_persistent()`

**Data Flow:**

1. Claude Code sets `$CLAUDE_PLUGIN_DATA` to a per-plugin persistent directory
   before invoking any hook.
2. `get_plugin_data_dir(project: str) -> Path` in `utils.py`:
   - Reads `os.environ.get("CLAUDE_PLUGIN_DATA", "")`.
   - If non-empty, returns `Path(CLAUDE_PLUGIN_DATA) / safe_project_name(project)`.
   - If empty (env var missing), falls back to
     `Path("/tmp") / f"zie-{safe_project_name(project)}-persistent"` and logs a
     stderr warning: `[zie-framework] CLAUDE_PLUGIN_DATA not set, using /tmp fallback`.
   - Calls `path.mkdir(parents=True, exist_ok=True)` before returning.
3. `safe_write_persistent(path: Path, content: str) -> bool` mirrors the
   existing `safe_write_tmp()` contract (symlink guard + atomic write via
   `os.replace()`). Returns `True` on success, `False` on symlink or `OSError`.
4. `persistent_project_path(name: str, project: str) -> Path` convenience wrapper
   (mirrors `project_tmp_path`): calls `get_plugin_data_dir(project) / name`.
5. `wip-checkpoint.py` replaces `project_tmp_path("edit-count", cwd.name)` with
   `persistent_project_path("edit-count", cwd.name)` and `safe_write_tmp()` with
   `safe_write_persistent()`. Edit counter now survives session restart.
6. `session-learn.py` replaces manual `~/.claude/projects/<project>/pending_learn.txt`
   path with `persistent_project_path("pending_learn.txt", project)`. No
   behaviour change for callers (session-resume still reads it).
7. `session-resume.py` must be updated to read `pending_learn.txt` from the new
   path. It calls `get_plugin_data_dir(project_name) / "pending_learn.txt"` using
   the same fallback logic.
8. `session-cleanup.py` already globs `/tmp/zie-<project>-*` only — no change
   needed, but a clarifying comment should be added noting that persistent data
   is intentionally excluded.
9. `settings.json`: Claude Code reads this at plugin load time. The `agent:` key
   activates a default agent. Ship as `{"agent": ""}` (empty string = no default
   agent) so the file is valid and future activation requires only filling the
   value, not creating a new file.

**Edge Cases:**
- `CLAUDE_PLUGIN_DATA` set but directory not writable: `safe_write_persistent()`
  catches `OSError`, returns `False`, logs to stderr — hook still exits 0.
- `CLAUDE_PLUGIN_DATA` set to a path that is a symlink itself: `get_plugin_data_dir()`
  does NOT guard against this (the env var is trusted as set by Claude Code);
  only the final write target is checked for symlink in `safe_write_persistent()`.
- Existing `pending_learn.txt` at the old `~/.claude/projects/<project>/` path:
  no migration required; `session-resume.py` will simply not find it on first
  session after upgrade and will resume without the stale context — safe.
- `CLAUDE_PLUGIN_DATA` path contains spaces or special characters: `Path()`
  handles this natively; no manual quoting needed.
- Two concurrent hooks writing the same persistent file: `os.replace()` is
  atomic on POSIX; last writer wins, no corruption.
- Project name with non-alphanumeric characters: already handled by
  `safe_project_name()` which is reused unchanged.
- `settings.json` `agent:` key left empty: Claude Code treats empty string as
  no default agent — plugin loads normally without activating an agent.

**Out of Scope:**
- Defining an actual default agent command or populating `agent:` with a value
  (that is a separate backlog item when a `zie-implement-mode` agent is designed).
- Migrating `auto-test.py` debounce state to persistent storage (debounce is
  intentionally session-scoped; persisting it would cause missed test runs after
  restart).
- Archiving subagent logs to `CLAUDE_PLUGIN_DATA` (mentioned in backlog as a
  candidate but no subagent log exists yet — deferred until subagent log feature
  is built).
- Encryption or access control on persistent data (plain files, same trust model
  as existing `/tmp` paths).
- Exposing `CLAUDE_PLUGIN_DATA` path to slash commands or skills.
