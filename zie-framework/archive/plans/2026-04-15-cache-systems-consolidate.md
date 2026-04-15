---
date: 2026-04-15
status: approved
slug: cache-systems-consolidate
---

## Steps

1. **Extend CacheManager with mtime invalidation** — Add `invalidation` param to `set()` and `get_or_compute()`: `"ttl"` (default), `"mtime"`, or `"session"`. For `"mtime"`, store `source_path` and `mtime` in entry; on `get()`, re-stat the file and invalidate on mismatch. For `"session"`, set `expires_at` to `float("inf")` (cleared only by `clear_session()`).

2. **Add `CacheManager.set_flag()` / `CacheManager.has_flag()`** — Lightweight boolean helpers for `/tmp` flag replacement: `set_flag("compact-tier-1", session_id)` and `has_flag("compact-tier-1", session_id)`. Stored as `{value: True, invalidation: "session"}` entries.

3. **Migrate `read_roadmap_cached()`** — Replace `utils_roadmap.py` `read_roadmap_cached`, `get_cached_roadmap`, `write_roadmap_cache` with `CacheManager.get_or_compute("roadmap", sid, compute_fn, invalidation="mtime", source_path=roadmap_path)`. Delete the three legacy functions.

4. **Migrate `knowledge-hash.py` mtime gate** — Replace `_mtime_cache_path`, `_read_mtime_cache`, `_write_mtime_cache` with `CacheManager.get_or_compute("knowledge_mtime", sid, compute_fn, invalidation="mtime", source_path=config_path)`. Keep `compute_hash()` unchanged.

5. **Migrate `/tmp` flags** — Replace `project_tmp_path()` calls in `sdlc-compact.py` (compact-snapshot, compact-tier), `stop-handler.py` (compact-tier, intent-sprint-flag), `intent-sdlc.py` (intent-dedup, intent-sprint-flag, last-test), `subagent-context.py` (session-context), `design-tracker.py` (design-mode), `stop-capture.py` (brainstorm-active, design-mode). Use `set_flag`/`has_flag` or `set`/`get` with `invalidation="session"`.

6. **Simplify `session-cleanup.py`** — Remove the `zie-*/` directory cleanup loop (legacy roadmap cache). Keep the `zie-{project}-*` glob for remaining `/tmp` flags. Add `CacheManager.clear_session(session_id)` call.

7. **Fix compact-tier naming** — Already handled by step 5 (flags move to CacheManager). Remove the old `project_tmp_path` calls entirely.

## Tests

- `test_cache_manager.py` — Add tests for: mtime invalidation (file change invalidates), session-scoped entries (persist until `clear_session`), `set_flag`/`has_flag` round-trip, `clear_session` removes session flags but not other sessions' entries.
- `test_utils_roadmap.py` — Verify `read_roadmap_cached` delegates to CacheManager (mock CacheManager, assert no `/tmp` files created).
- `test_knowledge_hash.py` — Verify mtime gate uses CacheManager instead of `/tmp` file.
- Integration: run `session-cleanup.py` and verify no orphaned `/tmp/zie-*` dirs remain.

## Acceptance Criteria

- All `/tmp/zie-{sid}/roadmap-cache.json` and `/tmp/zie-kh-*.mtime` files are no longer created
- ROADMAP is read at most once per session (CacheManager hit across all hooks)
- `knowledge-hash.py` mtime gate uses CacheManager, not a separate `/tmp` file
- 6+ `/tmp` flags replaced with CacheManager session-scoped entries
- `session-cleanup.py` has no legacy roadmap-cache cleanup loop
- `project_tmp_path()` usage reduced from 20+ to <10 (one-off coordination only)
- All existing tests pass; new tests cover mtime and session invalidation modes