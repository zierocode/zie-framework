---
approved: false
approved_at:
backlog: backlog/github-actions-ci.md
---

# CI/CD via GitHub Actions — Design Spec

**Problem:** zie-framework has no automated CI. Tests only run locally. A developer who forgets `make test` before pushing can introduce regressions to `dev` or `main` undetected. The test suite has 2535 unit tests — automated enforcement is valuable.

**Approach:** Add a single GitHub Actions workflow file (`.github/workflows/ci.yml`) that runs `make test-unit` on every push to `main`/`dev` and on every pull request targeting those branches. No secrets required. Python version pinned to match `.python-version` or `pyproject.toml`. Uses `actions/setup-python` with pip cache.

**Non-goals:** No deployment, no coverage upload, no matrix testing across Python versions, no AI-driven code review.

**Components:**
- Create: `.github/workflows/ci.yml` — Python CI workflow with unit test job
- No changes to Makefile, tests, or framework code

**Workflow design:**
```yaml
name: CI
on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
          cache: pip
      - run: pip install pytest pyyaml
      - run: make test-unit
```

**Acceptance Criteria:**
- AC1: `.github/workflows/ci.yml` exists with correct trigger (push + PR on main/dev)
- AC2: Workflow runs `make test-unit` (not integration tests)
- AC3: Python version matches `.python-version` if it exists, else `3.x`
- AC4: Pip cache configured
- AC5: Workflow passes cleanly on the current codebase
