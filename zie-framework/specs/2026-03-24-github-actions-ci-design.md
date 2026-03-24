---
approved: true
approved_at: 2026-03-24
backlog: backlog/github-actions-ci.md
---

# CI/CD via GitHub Actions — Design Spec

**Problem:** There is no automated CI. Tests only run locally. Regressions can be pushed to `dev` or `main` without detection unless the developer manually runs `make test` before every push.

**Approach:** Create a single GitHub Actions workflow file that runs `make test` on every push to `main` and `dev`, and on every pull request targeting either branch. Use the Python version from the project's existing config. No secrets beyond the default `GITHUB_TOKEN` are required.

**Components:**
- Create: `.github/workflows/ci.yml` — trigger on `push` to `main`/`dev` and `pull_request` targeting either; steps: checkout, setup-python (version from `.python-version` or `pyproject.toml`), install deps (`pip install -r requirements.txt -r requirements-dev.txt` or equivalent), run `make test`

**Acceptance Criteria:**
- [ ] Workflow runs on push to `main` and `dev`
- [ ] Workflow runs on pull requests targeting `main` or `dev`
- [ ] `make test` failure causes the workflow to fail (non-zero exit → red check)
- [ ] `make test` success causes the workflow to pass (green check)
- [ ] Python version matches the project's existing configuration
- [ ] No additional secrets required beyond `GITHUB_TOKEN`
- [ ] Workflow file is valid YAML (passes `actionlint` or equivalent)

**Out of Scope:**
- Deployment steps
- Coverage reporting or badge generation
- Matrix testing across multiple Python versions
- Caching pip dependencies (can be added later as optimization)
