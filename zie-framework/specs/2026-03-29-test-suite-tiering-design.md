---
approved: true
approved_at: 2026-03-29
backlog: backlog/test-suite-tiering.md
---

# Test Suite Tiering — Design Spec

**Problem:** The test suite has grown to 1,601 tests, slowing down local dev feedback loops. Developers skip `make test-unit` when it takes 30+ seconds, breaking the TDD loop.

**Approach:** Implement a two-tier test system: `make test-fast` runs only changed-file-related tests during RED/GREEN phases for instant feedback, while `make test-ci` runs the full suite before commit. No tests are removed or coverage lost—just smarter test selection.

**Components:**
- Makefile (add `test-fast`, `test-ci` targets)
- tdd-loop skill (reference `make test-fast` in RED/GREEN, `make test-ci` in REFACTOR)
- CLAUDE.md (document when to use each target)
- Test discovery mechanism (map changed files → related test files via `git diff --name-only`)

**Data Flow:**
1. Developer runs `make test-fast` after writing RED test or GREEN code
2. Makefile runs `git diff --name-only` to find changed files
3. Map changed files to related test files using this explicit convention:
   - `hooks/foo.py` → try `tests/unit/test_hooks_foo.py`, then `tests/unit/test_foo.py` (first match wins)
   - `commands/*.md` → no unit test mapping (markdown files have no unit tests)
   - Any other file with no match found → run full `make test-unit` as fallback (never skip tests silently)
4. Run pytest on matched tests + `--lf` (last-failed) to catch regressions
5. Before commit, developer runs `make test-ci` to verify full suite passes
6. CI/pre-commit hook uses `make test-ci` (full suite, coverage gate)

**Edge Cases:**
- File with no corresponding test file (e.g., `VERSION`, `.env`) → skip gracefully
- Test file names don't follow convention (e.g., `tests/unit_foo_bar.py`) → require mapping or manual override
- `git diff` on fresh clone (no HEAD) → fallback to running full suite
- Tests depend on setup/teardown in `conftest.py` → test discovery must preserve pytest fixtures
- Last-failed cache stale or corrupt → `pytest --lf` falls back to full run (safe)

**Out of Scope:**
- Splitting tests into separate directories (tests/unit/, tests/integration/) — use pytest markers instead
- Coverage reduction — test-fast still uses coverage measurement for full suite
- Selective skip of integration tests in test-fast (use -m flag separately if needed)
- CI-specific optimizations beyond full suite run
- Parallel test execution (pytest-xdist) — deferred for future optimization

**Testability:**
- `make test-fast` with no changes runs at least the last-failed suite
- `make test-fast` on a single changed file (e.g., `hooks/intent_sdlc.py`) runs `tests/test_intent_sdlc.py` + last-failed
- `make test-ci` runs full suite with coverage gate (>=50%)
- Both targets exit with non-zero on test failure
- Acceptance: timing improvement measurable (time `make test-fast` vs `make test-unit`)
