---
approved: true
approved_at: 2026-03-29
backlog: backlog/coverage-make-clean.md
---

# Coverage Artifacts — Design Spec

**Problem:** `make clean` removes pytest cache and compiled Python files but leaves `.coverage`, `coverage.xml`, and `htmlcov/` (coverage artifacts), causing stale data to accumulate and confusing reports that reference deleted files.

**Approach:** Add three coverage artifact patterns to the `clean` target in the Makefile: remove `.coverage` file, `coverage.xml`, and the `htmlcov/` directory on `make clean`.

**Components:**
- `Makefile` (lines 121-125, clean target) — existing target, update only

**Data Flow:**
1. User runs `make clean`
2. Script finds and removes `__pycache__` directories (existing)
3. Script finds and removes `.pytest_cache` directories (existing)
4. Script finds and removes `*.pyc` files (existing)
5. Script finds and removes `.coverage` file (new)
6. Script finds and removes `coverage.xml` file (new)
7. Script finds and removes `htmlcov/` directory (new)
8. Script calls `_clean-extra` hook (existing pattern)

**Edge Cases:**
- `.coverage` may not exist (no coverage run yet) — `find -delete` is silent for missing files, so this is safe
- `coverage.xml` may not exist (coverage not exported) — also silent
- `htmlcov/` may not exist (HTML report never generated) — also silent
- Multiple hook runs generate multiple `.coverage.*` files — glob `.*` captures all variants

**Out of Scope:**
- Changing the behavior of `coverage run`, `coverage combine`, or `coverage report` commands
- Modifying test configuration (`.coveragerc`)
- Adding new test commands or test infrastructure
- Documenting coverage workflow (already in README + CLAUDE.md)
