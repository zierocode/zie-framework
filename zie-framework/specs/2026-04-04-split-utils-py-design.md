# Spec: Split utils.py into Sub-Modules

**Date**: 2026-04-04
**Status**: Draft
**Feature**: split-utils-py

---

## Problem

`hooks/utils.py` is a 738-line monolithic module serving five distinct
concerns: config loading, I/O helpers, roadmap parsing/caching, safety
patterns, and event/hook utilities. Any hook importing one function drags
in all compile-time dependencies (e.g. `COMPILED_BLOCKS`, `urllib.request`).
This makes the module hard to test in isolation and violates single-responsibility.

---

## Approach

**Approach B — one-pass direct migration.**
All 18+ hook `from utils import …` lines are updated to import from the
correct sub-module. All 5 test files that import from `utils` are updated.
`utils.py` is deleted after migration. No facade is kept.

---

## New Module Definitions

### `utils_config.py`
Config loading and validation.

| Symbol | Type |
| --- | --- |
| `CONFIG_SCHEMA` | `dict` — key → (default, type) |
| `CONFIG_DEFAULTS` | `dict` — string defaults for known config keys |
| `validate_config(config)` | Fill schema keys with typed defaults |
| `load_config(cwd)` | Read + merge + validate `zie-framework/.config` |

### `utils_io.py`
File I/O helpers (tmp + persistent storage tiers).

| Symbol | Type |
| --- | --- |
| `atomic_write(path, content)` | Atomic rename-based write, 0o600 |
| `safe_write_tmp(path, content)` | Symlink-safe atomic write to tmp |
| `safe_write_persistent(path, content)` | Symlink-safe atomic write to persistent |
| `project_tmp_path(name, project)` | Project-scoped `/tmp/zie-<project>-<name>` |
| `get_plugin_data_dir(project)` | `$CLAUDE_PLUGIN_DATA/<project>` with fallback |
| `persistent_project_path(name, project)` | `get_plugin_data_dir(project) / name` |
| `is_zie_initialized(cwd)` | True if `cwd/zie-framework/` is a dir |
| `get_project_name(cwd)` | Sanitized `cwd.name` |
| `safe_project_name(project)` | Replace non-alphanumeric with `-` |

### `utils_roadmap.py`
ROADMAP parsing, caching, ADR caching, and mtime gate helpers.

| Symbol | Type |
| --- | --- |
| `SDLC_STAGES` | `list[str]` |
| `parse_roadmap_section(roadmap_path, section_name)` | Extract items from named `##` section |
| `parse_roadmap_section_content(content, section_name)` | Same but operates on string |
| `parse_roadmap_now(roadmap_path, warn_on_empty)` | Extract `## Now` items |
| `parse_roadmap_ready(roadmap_path, warn_on_empty)` | Extract `## Ready` items |
| `read_roadmap_cached(roadmap_path, session_id, ttl, tmp_dir)` | Session-cached disk read |
| `get_cached_roadmap(session_id, ttl, tmp_dir)` | Return cached content or None |
| `write_roadmap_cache(session_id, content, tmp_dir)` | Write content to session cache |
| `compact_roadmap_done(roadmap_path, threshold, cutoff_months, archive_base)` | Archive old Done entries |
| `get_cached_git_status(session_id, key, ttl)` | Return cached git output or None |
| `write_git_status_cache(session_id, key, content)` | Write git output to cache |
| `get_cached_adrs(session_id, decisions_dir, tmp_dir)` | Return cached ADR content or None |
| `write_adr_cache(session_id, content, decisions_dir, tmp_dir)` | Write ADR content to cache |
| `compute_max_mtime(base_dir, pattern)` | Max mtime of matching files under dir |
| `is_mtime_fresh(max_mtime, written_at)` | True if no file newer than last write |

> **Note:** `compute_max_mtime` and `is_mtime_fresh` belong here because
> they exist exclusively to gate roadmap/ADR cache freshness. Placing them
> in `utils_io.py` would create a cross-dependency into roadmap concerns.

### `utils_safety.py`
Safety pattern constants compiled at import time.

| Symbol | Type |
| --- | --- |
| `BLOCKS` | `list[tuple[str, str]]` — (pattern, message) |
| `WARNS` | `list[tuple[str, str]]` — (pattern, message) |
| `COMPILED_BLOCKS` | Pre-compiled `BLOCKS` patterns |
| `COMPILED_WARNS` | Pre-compiled `WARNS` patterns |
| `normalize_command(cmd)` | Normalize whitespace + lowercase for matching |

### `utils_event.py`
Hook event I/O and session utilities.

| Symbol | Type |
| --- | --- |
| `read_event()` | Parse JSON from stdin; exits 0 on failure |
| `get_cwd()` | `CLAUDE_CWD` env var or `os.getcwd()` |
| `sanitize_log_field(value)` | Strip ASCII control chars from log values |
| `log_hook_timing(hook_name, duration_ms, exit_code, session_id)` | Append JSON timing entry |
| `call_zie_memory_api(url, key, endpoint, payload, timeout)` | POST to zie-memory API |

---

## Hook Import Updates

All 18+ hooks that currently do `from utils import …` update their imports
to the correct sub-module. This is a grep-and-replace operation — no logic
changes.

Hook-to-sub-module mapping (non-exhaustive; all hooks updated):

| Hook | Sub-modules used |
| --- | --- |
| `safety-check.py` | `utils_safety`, `utils_event`, `utils_io`, `utils_config` |
| `safety_check_agent.py` | `utils_safety`, `utils_event`, `utils_io`, `utils_config` |
| `sdlc-permissions.py` | `utils_safety`, `utils_event` |
| `stopfailure-log.py` | `utils_event`, `utils_io`, `utils_roadmap` |
| `session-resume.py` | `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| `input-sanitizer.py` | `utils_event`, `utils_io` |
| `intent-sdlc.py` | `utils_event`, `utils_io`, `utils_roadmap` |
| `stop-guard.py` | `utils_event`, `utils_config`, `utils_io` |
| `task-completed-gate.py` | `utils_event`, `utils_config`, `utils_io` |
| `notification-log.py` | `utils_event`, `utils_io` |
| `failure-context.py` | `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| `subagent-stop.py` | `utils_event`, `utils_io` |
| `wip-checkpoint.py` | `utils_event`, `utils_io`, `utils_roadmap` |
| `subagent-context.py` | `utils_event`, `utils_roadmap` |
| `sdlc-compact.py` | `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| `auto-test.py` | `utils_event`, `utils_config`, `utils_io` |
| `session-cleanup.py` | `utils_event`, `utils_io` |
| `session-learn.py` | `utils_event`, `utils_io`, `utils_roadmap` |

---

## Test File Updates

The 5 test files (+ 2 additional files) that do `from utils import …` update
to the correct sub-module. No test logic changes — only import lines.

| Test file | Updated import target |
| --- | --- |
| `test_utils.py` | `utils_io`, `utils_event`, `utils_config` |
| `test_utils_helpers.py` | `utils_io` |
| `test_utils_ready.py` | `utils_roadmap` |
| `test_utils_sanitize.py` | `utils_config`, `utils_event` |
| `test_utils_write_permissions.py` | `utils_io` |
| `test_compact_roadmap_done.py` | `utils_roadmap` |
| `test_safety_check_precompile.py` | `utils_safety` |

---

## Acceptance Criteria

1. `hooks/utils.py` no longer exists after migration.
2. All 18+ hooks import exclusively from `utils_config`, `utils_io`,
   `utils_roadmap`, `utils_safety`, or `utils_event` — no import from `utils`.
3. All 7 test files import from the correct sub-module — no import from `utils`.
4. `make test-ci` passes with no new failures or coverage regressions.
5. No behavior changes: all public symbols are relocated, not renamed or
   altered.
6. Each sub-module is independently importable with only stdlib dependencies
   (no circular imports between sub-modules).

---

## Out of Scope

- Renaming any existing public symbol.
- Merging or refactoring hook logic.
- Adding new tests (existing tests cover the symbols; import path change is sufficient).
- Creating `__init__.py` package — sub-modules remain flat files in `hooks/`.
