---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-dependabot-setup.md
spec: specs/2026-03-24-audit-dependabot-setup-design.md
---

# Dependabot Setup — Implementation Plan

**Goal:** Create `.github/dependabot.yml` watching the `pip` and `github-actions` ecosystems to satisfy OpenSSF Scorecard's `Dependency-Update-Tool` check.
**Architecture:** New config file in a new `.github/` directory. No Python code changes. Weekly schedule covers both ecosystems; the `pip` entry scans the repo root for `requirements*.txt` and `pyproject.toml`; the `github-actions` entry is forward-compatible and activates once workflows are added.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `.github/dependabot.yml` | Dependabot config watching pip and github-actions ecosystems |

## Task 1: Create .github/dependabot.yml

**Acceptance Criteria:**
- `.github/dependabot.yml` exists at the repository root
- The file is valid YAML with `version: 2`
- Two `updates` entries: `pip` and `github-actions`, both with `directory: "/"` and `schedule.interval: weekly`
- `open-pull-requests-limit: 5` is set on both entries
- The file is committed to the repository (Dependabot reads it from the default branch)

**Files:**
- Create: `.github/dependabot.yml`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — config file creation. Verified manually by confirming the file exists with correct YAML structure.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  Create `.github/` directory, then create `.github/dependabot.yml`:

  ```yaml
  version: 2
  updates:
    - package-ecosystem: pip
      directory: "/"
      schedule:
        interval: weekly
      open-pull-requests-limit: 5

    - package-ecosystem: github-actions
      directory: "/"
      schedule:
        interval: weekly
      open-pull-requests-limit: 5
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm no trailing whitespace. Confirm YAML is parseable with `python3 -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"`.
  Run: `make test-unit` — still PASS
