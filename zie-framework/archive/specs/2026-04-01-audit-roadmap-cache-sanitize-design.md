---
slug: audit-roadmap-cache-sanitize
status: draft
date: 2026-04-01
---

# Spec: Sanitize roadmap cache session_id and align with cleanup convention

## Problem

`get_cached_roadmap` and `write_roadmap_cache` in `hooks/utils.py` build their
cache path as `Path(f"/tmp/zie-{session_id}/roadmap.cache")` — three separate
bugs that every other cache helper in the same file already avoids:

1. **No session_id sanitization** — a crafted session_id containing `../` or
   other shell-special characters can traverse outside the intended namespace.
   `get_cached_git_status`/`write_git_status_cache` both call
   `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)` before building the path;
   the roadmap pair does not.

2. **Hardcoded `/tmp/`** — all other caching helpers use
   `tempfile.gettempdir()`, which is portable and is also the injection point
   used by the test suite (`tmp_dir` parameter). The hardcoded path bypasses
   both.

3. **Cleanup never fires** — `session-cleanup.py` globs
   `zie-{safe_project}-*` inside `tempfile.gettempdir()`. Roadmap cache dirs
   are named `zie-{session_id}/` — a different prefix scheme — so they never
   match the glob and accumulate indefinitely across sessions.

## Proposed Solution

Bring `get_cached_roadmap`/`write_roadmap_cache` in line with the established
`get_cached_git_status`/`write_git_status_cache` pattern:

- Apply `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)` to produce `safe_id`.
- Replace the hardcoded `/tmp/` with `tempfile.gettempdir()`.
- Accept an optional `tmp_dir` parameter (default `None`; when set, overrides
  `tempfile.gettempdir()`) so existing tests can inject a controlled path.

The resulting cache path becomes:
`{tmp_dir or tempfile.gettempdir()}/zie-{safe_id}/roadmap.cache`

No changes are needed to `session-cleanup.py` because after the fix, the
`zie-{safe_id}/` directory name still does not match the
`zie-{safe_project}-*` glob. To make cleanup work we extend
`session-cleanup.py` to also glob `zie-{safe_session_id}-*` directories —
but the session_id is not available in the stop hook's event payload by
default. Instead, align the cache directory naming: rename the roadmap cache
dir to use the project-scoped convention already employed by `project_tmp_path`
(i.e., `zie-{safe_project}-roadmap-{safe_id}.cache` flat file rather than a
subdirectory). This matches the glob without any changes to `session-cleanup.py`.

**Chosen approach** (simpler, no cleanup script changes):
- Cache file path: `{tmp_dir}/zie-{safe_project}-roadmap.cache`
  where `safe_project = safe_project_name(cwd.name)`.

Wait — callers pass only `session_id`, not `cwd`. Inspecting callers: the
function is called from `failure-context.py` and similar hooks that already
have `session_id`. Keeping the directory approach (`zie-{safe_id}/roadmap.cache`)
preserves the existing API shape; we only need to additionally glob those dirs
in cleanup.

**Final chosen approach** (minimal diff, explicit cleanup extension):

1. In `utils.py`: sanitize `session_id` and use `tempfile.gettempdir()` in
   both `get_cached_roadmap` and `write_roadmap_cache`. Add optional `tmp_dir`
   parameter. Cache path: `{tmp_dir}/zie-{safe_id}/roadmap.cache`.

2. In `session-cleanup.py`: after the existing project-glob, add a second glob
   for `zie-*` directories that contain a `roadmap.cache` file, bounded to
   dirs whose names match the `zie-{alphanum-dash}-*` shape — or simply glob
   all `zie-*/roadmap.cache` files and remove them plus their parent dirs
   (if empty afterwards). Scoped to `tempfile.gettempdir()` only.

## Acceptance Criteria

- [ ] AC1 — `write_roadmap_cache` applies `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)` before constructing the cache path.
- [ ] AC2 — `get_cached_roadmap` applies the same sanitization before constructing the cache path.
- [ ] AC3 — Both functions use `tempfile.gettempdir()` (not hardcoded `/tmp/`) as the base, with an optional `tmp_dir` parameter that overrides it when provided.
- [ ] AC4 — `session-cleanup.py` removes leftover `zie-{session_id}/roadmap.cache` files (and their parent dirs when empty) from `tempfile.gettempdir()` on session end, without touching any non-roadmap dirs.
- [ ] AC5 — All existing unit tests for `get_cached_roadmap`/`write_roadmap_cache` pass with a `tmp_dir` injection; no test writes to a real `/tmp/` path.
- [ ] AC6 — A new unit test confirms that a session_id containing `../` is sanitized to `--` and does not escape the intended `tempfile.gettempdir()` base.
- [ ] AC7 — `session-cleanup.py` integration test (or existing test) confirms roadmap cache dirs are removed on cleanup.

## Out of Scope

- Changing the cache TTL or cache format.
- Refactoring `get_cached_adrs` or other cache helpers (they are already correct).
- Making `session-cleanup.py` clean up any cache other than the roadmap cache dirs introduced here.
- Switching to a project-scoped flat-file naming for the roadmap cache (deferred — would require updating all callers).
