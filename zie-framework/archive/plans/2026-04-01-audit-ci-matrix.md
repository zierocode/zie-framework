---
slug: audit-ci-matrix
status: approved
approved: true
date: 2026-04-01
---

# Plan: CI Matrix — Python 3.11 + 3.12 on macOS

## Overview

Add `.github/workflows/ci.yml` with a matrix strategy covering Python 3.11
and 3.12 on `macos-latest`. The existing `make test-ci` target is the only
test step — no custom pip commands.

Spec: `zie-framework/specs/2026-04-01-audit-ci-matrix-design.md`

---

## Tasks

### Task 1 — Create `.github/workflows/ci.yml`

**Before:** File does not exist.

**After — full file content:**

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  test:
    name: "Python ${{ matrix.python-version }} / ${{ matrix.os }}"
    runs-on: ${{ matrix.os }}

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
        os: ["macos-latest"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: make setup

      - name: Run full test suite
        run: make test-ci
```

**Design rationale:**

| Decision | Reason |
| --- | --- |
| `fail-fast: false` | Both legs run fully — failures on 3.11 and 3.12 both visible |
| `macos-latest` only | Dev platform is darwin; ubuntu addition is a separate backlog item |
| `actions/checkout@v4` | Current stable major |
| `actions/setup-python@v5` | Current stable major |
| `make setup` | Mirrors local dev: installs git hooks + python deps |
| `make test-ci` | Full suite + coverage gate — same as pre-commit |
| All branches | Catches breakage on feature branches before merge |

---

### Task 2 — Validate YAML syntax locally

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`

---

## Verification

After pushing to `dev`:
- GitHub Actions queues 2 jobs: `Python 3.11 / macos-latest` and `Python 3.12 / macos-latest`
- Both must reach status `success`
- If either fails, the failure is in the test suite — fix via `/zie-fix`

---

## Test Strategy

**Pyramid level:** Integration (CI pipeline execution)

No new unit tests required — the deliverable is a YAML config file. Correctness
criterion: `make test-ci` passes on both Python 3.11 and 3.12.

---

## Rollout

1. Create `.github/workflows/` directory if it doesn't exist.
2. Create `.github/workflows/ci.yml` per Task 1.
3. Run YAML lint (Task 2) — must print `YAML OK`.
4. Commit and push to `dev`.
5. Confirm both matrix legs go green in GitHub Actions.
6. Rollback: delete `.github/workflows/ci.yml` — no other files affected.

---

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` exists at repo root.
- [ ] Matrix covers Python 3.11 and 3.12.
- [ ] OS is `macos-latest`.
- [ ] Steps: `make setup` then `make test-ci` only.
- [ ] Both matrix legs pass green in GitHub Actions.
- [ ] YAML is valid (yaml.safe_load confirms no parse error).
