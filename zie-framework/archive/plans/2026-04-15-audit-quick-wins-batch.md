---
date: 2026-04-15
status: approved
slug: audit-quick-wins-batch
---

# Audit Quick Wins Batch — Implementation Plan

## Steps

1. **Fix hardcoded test paths** — In `test_utils_submodules_importable.py:7`, replace `REPO_ROOT = "/Users/zie/..."` with `REPO_ROOT = Path(__file__).parent.parent.parent`. In `test_knowledge_hash_now.py:9,17,25,35`, replace `cwd="/Users/zie/..."` with `cwd=str(Path(__file__).parent.parent.parent)`.

2. **Sync versions** — Update PROJECT.md version line from `1.30.0` to `1.30.1`. Update SECURITY.md supported versions table from `1.4.x` to `1.30.x`. Confirm VERSION already reads `1.30.1`.

3. **Refresh stale docs** — In `components.md`, remove rows for stop-guard.py, compact-hint.py, sdlc-context.py; rename intent-detect.py → intent-sdlc.py entry. In `config-reference.md`, remove stop-guard.py reference in subprocess_timeout_s row.

4. **Rename test_stop_guard.py** — `git mv tests/test_stop_guard.py tests/unit/test_stop_handler.py`. Update internal references from `stop-guard` to `stop-handler` where they test the merged module. Remove assertion that `stop-guard.py` must appear in components.md (it no longer exists).

5. **Move misplaced test files** — `git mv` the 9 root `tests/test_*.py` files to `tests/unit/`. Fix any import paths that break after the move.

6. **Move misplaced integration test** — `git mv tests/unit/test_test_fast_acceptance.py tests/integration/`.

7. **Replace time.sleep() in tests** — In `test_cache_manager.py:94,107` (1.1s sleeps), `test_nudges_stop_guard.py:47`, `test_utils_roadmap_cache_mtime.py:28` — mock time or use freezegun instead of real sleeps.

8. **Suppress TestLookupCache collection warning** — Add `__test__ = False` to `TestLookupCache` class in `hooks/auto-test.py`.

9. **session-learn atomic write** — Replace `open(_log_path, "a")` with `atomic_write` append pattern at line 101 of `session-learn.py`.

10. **session-stop atomic write + symlink validation** — Replace `write_text()` + `chmod` with `atomic_write`. Add check that symlink target is within memory directory.

11. **Extract derive_stage()** — Move `derive_stage()` from `intent-sdlc.py` to `utils_roadmap.py`. Update imports in `intent-sdlc.py`, `session-stop.py`, `session-learn.py`.

12. **config-drift read_event** — Replace `sys.stdin.read()` + `json.loads()` with `utils_event.read_event()` in `config-drift.py`.

13. **Remove orphaned pending_learn write** — Remove the `pending_learn_file.write_text()` block in `session-learn.py` (lines ~264-265) since session-resume only reads from project-local path.

14. **Fix ADR-012 reference** — In `CLAUDE.md`, replace `ADR-012` with `ADR-022/ADR-063`.

## Tests

- Run `make test-unit` after each step to catch regressions
- Verify `test_utils_submodules_importable` passes with relative path on any machine
- Verify `test_knowledge_hash_now` passes with relative path
- Verify `test_stop_handler` (renamed) passes
- Verify moved test files are discovered by pytest
- Verify `time.sleep` removal doesn't break cache TTL tests

## Acceptance Criteria

- `grep -r "/Users/zie/Code/zie-framework" tests/` returns zero hits
- `VERSION`, `PROJECT.md`, `SECURITY.md` all show `1.30.1` or `1.30.x`
- `components.md` has no references to stop-guard, compact-hint, or sdlc-context
- `config-reference.md` has no references to stop-guard
- `test_stop_guard.py` no longer exists; `test_stop_handler.py` exists and passes
- All root `tests/test_*.py` files moved to `tests/unit/` or `tests/integration/`
- `make test-ci` passes cleanly (no collection warnings, no flaky sleeps)