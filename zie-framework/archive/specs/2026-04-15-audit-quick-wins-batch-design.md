---
date: 2026-04-15
status: approved
slug: audit-quick-wins-batch
---

# Audit Quick Wins Batch — Design Spec

## Problem

Five audit findings from 2026-04-14 each need XS-S effort but individually waste sprint overhead. Batching them: (1) hardcoded `/Users/zie/Code/zie-framework` paths in tests break CI, (2) VERSION/PROJECT.md/SECURITY.md version drift, (3) stale docs reference deleted hooks, (4) test quality issues (dead refs, misplaced files, flaky sleeps), (5) code quality wins (atomic writes, derive_stage dedup, config-drift stdin parse, pending_learn orphan, ADR-012 ref).

## Solution

**Hardcoded paths** — Replace 5 occurrences in `test_utils_submodules_importable.py` and `test_knowledge_hash_now.py` with `Path(__file__).parent.parent.parent`-relative resolution.

**Version sync** — Set PROJECT.md version to 1.30.1; update SECURITY.md supported versions table to current major.minor.

**Stale docs** — Remove stop-guard.py, compact-hint.py, sdlc-context.py rows from components.md; update intent-detect → intent-sdlc; remove stop-guard reference in config-reference.md.

**Test quality** — Rename `test_stop_guard.py` → `test_stop_handler.py`, update internal refs; move 9 root `tests/test_*.py` files to `tests/unit/`; replace `time.sleep()` with mock/patch; move `test_test_fast_acceptance.py` to `tests/integration/`; add `__test__ = False` to TestLookupCache.

**Quick wins** — Use `atomic_write` in session-learn pattern-log; use `atomic_write` in session-stop; add symlink validation; extract `derive_stage()` to `utils_roadmap`; replace config-drift manual stdin parse with `read_event()`; remove orphaned pending_learn write in session-learn; update ADR-012 reference in CLAUDE.md → ADR-022/ADR-063.

## Rough Scope

**In**: All items above. **Out**: Any new features, refactors beyond listed scope, hook architecture changes.

## Files Changed

- `tests/unit/test_utils_submodules_importable.py`, `tests/unit/test_knowledge_hash_now.py` — hardcoded paths
- `VERSION`, `zie-framework/PROJECT.md`, `SECURITY.md` — version sync
- `zie-framework/project/components.md`, `zie-framework/project/config-reference.md` — stale docs
- `tests/test_stop_guard.py` → `tests/unit/test_stop_handler.py`, 9 root test files → `tests/unit/`, `tests/unit/test_test_fast_acceptance.py` → `tests/integration/`
- `hooks/session-learn.py`, `hooks/session-stop.py`, `hooks/intent-sdlc.py`, `hooks/config-drift.py`, `hooks/utils_roadmap.py`, `CLAUDE.md`