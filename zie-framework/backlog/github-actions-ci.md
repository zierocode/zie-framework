# CI/CD via GitHub Actions

## Problem

There is no automated CI — tests only run locally. Regressions can be pushed
to `dev` or `main` without detection unless the developer remembers to run
`make test` manually before every push.

## Motivation

A GitHub Actions workflow that runs `make test` on every push and pull request
catches regressions immediately and creates a visible green/red status on each
commit. Zero configuration needed beyond a single workflow file.

## Rough Scope

- Create `.github/workflows/ci.yml`
- Trigger on: `push` to `main` and `dev`, and on `pull_request`
- Steps: checkout, setup Python (match `.python-version` or pyproject.toml),
  install dependencies (`pip install -r requirements.txt` or equivalent),
  run `make test`
- No secrets required beyond the default `GITHUB_TOKEN`
- Out of scope: deployment, coverage reporting, matrix testing across Python versions
