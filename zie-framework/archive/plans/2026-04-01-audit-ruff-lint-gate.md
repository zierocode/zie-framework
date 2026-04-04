---
slug: audit-ruff-lint-gate
status: approved
approved: true
date: 2026-04-01
---

# Plan: Ruff Lint Gate

## Overview

Add `ruff` as the enforced Python linter. Deliverables:
1. `pyproject.toml` — ruff config (E, F, I rules; pin 0.11.2)
2. `requirements-dev.txt` — add `ruff==0.11.2`
3. `Makefile` — add `lint` and `lint-fix` targets; `ci` runs `lint` then `test-ci`
4. `.github/workflows/ci.yml` — independent `lint` job
5. `.pre-commit-config.yaml` — create with astral-sh/ruff-pre-commit v0.11.2
6. Fix all existing violations so `make lint` exits 0
7. Update `CLAUDE.md` dev commands section

## File Map

| File | Change |
| --- | --- |
| `pyproject.toml` | Create |
| `requirements-dev.txt` | Modify — add ruff pin |
| `Makefile` | Modify — add lint targets, wire into ci |
| `.github/workflows/ci.yml` | Modify — add independent lint job |
| `.pre-commit-config.yaml` | Create |
| `hooks/*.py` | Modify — fix any ruff violations found in Task 6 |
| `CLAUDE.md` | Modify — add lint targets to dev commands table |

## Tasks

### Task 1 — Create `pyproject.toml` with ruff config

**Before:** File does not exist.

**After — `pyproject.toml`:**

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["hooks"]
```

`E501` ignored per spec (line length not enforced). `line-length = 120` avoids false positives on longer hook lines.

### Task 2 — Pin ruff in `requirements-dev.txt`

**Before:**
```text
pytest>=9.0.2
pytest-cov>=7.1.0
coverage>=7.13.5
bandit>=1.9.4
commitizen>=4.13.9
```

**After:**
```text
pytest>=9.0.2
pytest-cov>=7.1.0
coverage>=7.13.5
bandit>=1.9.4
commitizen>=4.13.9
ruff==0.11.2
```

### Task 3 — Add `lint` / `lint-fix` targets to `Makefile`; wire into `ci`

**Add after the Dev section, before Release:**

```makefile
# ──────────────────────────────────────────────
# Lint
# ──────────────────────────────────────────────

lint:
	ruff check .

lint-fix:
	ruff check . --fix
```

**Update `ci` target:**

```makefile
# Before:
ci:
	$(MAKE) test-ci

# After:
ci:
	$(MAKE) lint
	$(MAKE) test-ci
```

### Task 4 — Add independent `lint` job to `.github/workflows/ci.yml`

**Before:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: make test-ci
```

**After:**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install ruff
        run: pip install ruff==0.11.2
      - name: Lint
        run: ruff check .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: make test-ci
```

`lint` job installs only ruff (fast). Independent of `test` job so failures surface in parallel.

### Task 5 — Create `.pre-commit-config.yaml`

**Before:** File does not exist.

**After:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.2
    hooks:
      - id: ruff
        args: [--fix]
```

`pre-commit` itself is opt-in — not added to `requirements-dev.txt`. Developers run `pip install pre-commit && pre-commit install` manually.

### Task 6 — Fix existing violations (RED → GREEN)

**RED:**
```bash
pip install ruff==0.11.2
ruff check .   # record all violations, confirm non-zero exit
```

**GREEN:**
```bash
ruff check . --fix           # auto-fix safe violations (unused imports, isort)
# manually fix any remaining violations
ruff check .                 # must exit 0
make test-ci                 # confirm no regressions from fixes
```

**Verify:**
```bash
grep -rn 're.compile\|# noqa' hooks/ | head -20  # review any suppressions
```

Violation fixes are committed as a separate commit from the gate infrastructure so the diff is reviewable.

### Task 7 — Update `CLAUDE.md` dev commands table

**Before (Development Commands section):**
```
make test-ci          # full suite with coverage gate — use before commit and in CI
```

**After:**
```
make lint             # run ruff lint check (fast, no I/O)
make lint-fix         # auto-fix safe ruff violations
make test-ci          # full suite with coverage gate — use before commit and in CI
```

## Test Strategy

No new unit tests required — `ruff check .` and `make lint` are the verification mechanism. The lint gate itself is the test.

**Acceptance verification per AC:**

| AC | Verified by |
| -- | ----------- |
| AC-1: `make lint` exits 0 | Task 6 GREEN step |
| AC-2: `make lint-fix` exits 0 | Task 3 + local run |
| AC-3: `make ci` runs lint | Task 3 Makefile diff |
| AC-4: pre-commit hook runs ruff | Task 5 + `pre-commit run ruff` |
| AC-5: ruff version pinned | Tasks 2, 4, 5 all pin 0.11.2 |
| AC-5 (CI job independent): | Task 4 — separate job block |
| AC-6: violations fixed first | Task 6 before Tasks 3-4 in rollout |

## Rollout Order

1. Task 1 — pyproject.toml (config must exist before lint runs)
2. Task 2 — requirements-dev.txt (pin ruff)
3. Task 6 — fix existing violations (do before wiring gate to avoid immediate CI failure)
4. Task 3 — Makefile targets
5. Task 4 — CI lint job
6. Task 5 — pre-commit config
7. Task 7 — CLAUDE.md update

Violation fixes (Task 6) go in a separate commit before the gate infrastructure (Tasks 3-5) to make the diff reviewable and avoid the gate failing on its first run.
