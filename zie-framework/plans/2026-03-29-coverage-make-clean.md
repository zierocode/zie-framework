---
approved: false
approved_at:
backlog: backlog/coverage-make-clean.md
spec: specs/2026-03-29-coverage-make-clean-design.md
---

# Coverage Artifacts — make clean — Implementation Plan

**Goal:** Extend the `clean` target in `Makefile` to also remove `.coverage`, `coverage.xml`, and `htmlcov/` so all test artifacts are wiped in one command.
**Architecture:** Single-file change — three `find`/`rm` statements appended to the existing `clean` target (lines 121-125). No new files, no new targets, no config changes.
**Tech Stack:** GNU Make, POSIX `find`, POSIX `rm`.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Add `.coverage`, `coverage.xml`, `htmlcov/` removal to `clean` target |

---

## Task 1: Extend `clean` target with coverage artifact removal

**Acceptance Criteria:**
- `make clean` removes `.coverage` (and `.coverage.*` variants) when present.
- `make clean` removes `coverage.xml` when present.
- `make clean` removes `htmlcov/` directory when present.
- `make clean` runs silently when none of those files exist (no error, no output).
- `make test-unit` followed by `make clean` leaves no coverage artifacts behind.

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**

  Add a shell-based integration test that:
  1. Creates stub artifacts (`.coverage`, `coverage.xml`, `htmlcov/`).
  2. Runs `make clean`.
  3. Asserts the stubs are gone.

  File: `tests/test_make_clean_coverage.sh` (executable shell script, run manually — not part of pytest suite because Makefile targets are outside pytest scope; acts as the "failing" reference before the fix).

  ```bash
  #!/usr/bin/env bash
  # tests/test_make_clean_coverage.sh
  # Manual RED-phase verification — run from repo root.
  set -euo pipefail
  ROOT="$(git rev-parse --show-toplevel)"
  cd "$ROOT"

  # Create stub artifacts
  touch .coverage
  touch coverage.xml
  mkdir -p htmlcov && touch htmlcov/index.html

  # Run clean (before fix — should leave artifacts behind)
  make clean >/dev/null 2>&1

  # Assert stubs still exist (pre-fix, RED state)
  FAIL=0
  [ -f .coverage ]       || { echo "UNEXPECTED: .coverage already removed"; FAIL=1; }
  [ -f coverage.xml ]    || { echo "UNEXPECTED: coverage.xml already removed"; FAIL=1; }
  [ -d htmlcov ]         || { echo "UNEXPECTED: htmlcov/ already removed"; FAIL=1; }

  if [ "$FAIL" -eq 0 ]; then
    echo "RED confirmed — artifacts survive make clean (fix not yet applied)"
  else
    echo "Something unexpected happened in RED phase"
    exit 1
  fi
  ```

  Run: `bash tests/test_make_clean_coverage.sh` — must print "RED confirmed".

- [ ] **Step 2: Implement (GREEN)**

  Edit `Makefile`, `clean` target (currently lines 121-125). Add three lines after the existing `find . -name "*.pyc"` line and before `$(MAKE) _clean-extra`:

  ```makefile
  clean: ## Remove cache files and build artifacts
  	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
  	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
  	find . -name "*.pyc" -delete 2>/dev/null; \
  	find . -name ".coverage" -delete 2>/dev/null; \
  	find . -name ".coverage.*" -delete 2>/dev/null; \
  	find . -name "coverage.xml" -delete 2>/dev/null; \
  	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null; \
  	$(MAKE) _clean-extra; true
  ```

  After editing, update `tests/test_make_clean_coverage.sh` GREEN assertions:

  ```bash
  # GREEN phase — run after fix is applied
  set -euo pipefail
  ROOT="$(git rev-parse --show-toplevel)"
  cd "$ROOT"

  touch .coverage
  touch coverage.xml
  mkdir -p htmlcov && touch htmlcov/index.html

  make clean >/dev/null 2>&1

  FAIL=0
  [ ! -f .coverage ]    || { echo "FAIL: .coverage still present"; FAIL=1; }
  [ ! -f coverage.xml ] || { echo "FAIL: coverage.xml still present"; FAIL=1; }
  [ ! -d htmlcov ]      || { echo "FAIL: htmlcov/ still present"; FAIL=1; }

  if [ "$FAIL" -eq 0 ]; then
    echo "GREEN — all coverage artifacts removed by make clean"
  else
    exit 1
  fi
  ```

  Run: `bash tests/test_make_clean_coverage.sh` — must print "GREEN".

  Run: `make test-unit` — must PASS (existing test suite unaffected).

- [ ] **Step 3: Refactor**

  No structural refactoring needed — the change is minimal and already idiomatic with the surrounding `clean` target style.

  Confirm idempotency: run `make clean` twice in a row — no errors on second run (all `2>/dev/null` guards ensure silence when files absent).

  Run: `make clean && make clean` — must succeed silently both times.
  Run: `make test-unit` — still PASS.
