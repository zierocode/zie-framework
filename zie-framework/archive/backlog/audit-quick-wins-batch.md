# audit-quick-wins-batch

## Problem

Multiple small audit findings from the 2026-04-14 audit each take XS-S effort but have meaningful impact. Individually speccing each one wastes sprint overhead. Batch them together for efficient implementation.

Includes: hardcoded test paths (tests fail on other machines/CI), stale docs (components.md references deleted hooks), test quality (orphaned test references, misplaced test files), and version sync (VERSION/PROJECT.md out of date).

## Rough Scope

- **audit-hardcoded-test-paths**: Replace hardcoded `/Users/zie/Code/zie-framework` paths in test files with `tmp_path` or `Path(__file__)`-relative paths
- **audit-stale-docs-refresh**: Update `components.md` to remove references to deleted hooks (stop-guard.py, compact-hint.py, sdlc-context.py) and renamed intent-detect.py
- **audit-test-quality-fixes**: Fix test_stop_guard.py reference to non-existent stop-guard.py, move 9 test files from `tests/` root to `tests/unit/` or `tests/integration/`
- **audit-version-sync**: Sync VERSION file and PROJECT.md to current v1.30.1
- **audit-quick-wins**: Remaining XS-effort fixes not covered above

## Priority

HIGH — tests are failing on other machines, version out of sync

## Merged From

- audit-quick-wins (XS effort batch)
- audit-hardcoded-test-paths (S effort)
- audit-stale-docs-refresh (S effort)
- audit-test-quality-fixes (S effort)
- audit-version-sync (XS effort)

Reason: All are small audit fixes. Individually speccing 5 XS-S items wastes sprint overhead. Batch together for efficient implementation.