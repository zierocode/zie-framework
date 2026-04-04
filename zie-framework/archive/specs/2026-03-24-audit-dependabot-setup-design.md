---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-dependabot-setup.md
---

# Dependabot Setup — Design Spec

**Problem:** No Dependabot configuration exists, so `pytest` and GitHub Actions
dependencies receive no automated update monitoring, failing OpenSSF
Scorecard's `Dependency-Update-Tool` check.

**Approach:** Create `.github/dependabot.yml` watching two ecosystems: `pip`
(for Python dev deps in `requirements-dev.txt` / `pyproject.toml`) and
`github-actions` (for any Actions workflows). Weekly schedule is sufficient
for a solo developer project.

**Components:**

- `.github/dependabot.yml` — new file (create `.github/` directory first)

**Data Flow:**

1. Create `.github/` directory if it does not exist.

2. Create `.github/dependabot.yml`:

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

3. No additional Dependabot config needed (no npm, no Docker).

**Edge Cases:**

- No `requirements-dev.txt` exists currently (dev deps managed in
  `pyproject.toml` or installed ad-hoc) — Dependabot will still scan and
  report if a `requirements*.txt` or `pyproject.toml` with `[dev-dependencies]`
  is present; otherwise the `pip` entry is a no-op until one is added
- No GitHub Actions workflows exist yet — `github-actions` entry is
  forward-compatible and harmless when no workflows are present
- If `.github/` is later populated with workflows, Dependabot activates
  automatically

**Out of Scope:**

- Renovate as alternative (Dependabot is simpler for a solo repo)
- Auto-merge configuration for Dependabot PRs
- OpenSSF Scorecard badge setup (separate item)
