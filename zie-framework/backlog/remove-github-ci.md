---
tags: [chore]
---

# Remove GitHub CI

## Problem

GitHub Actions workflows and Dependabot are configured but serve no real purpose — the project doesn't deploy anywhere. CI only runs lint+test on push/PR, and release-provenance generates SLSA attestations on tag push, but the sole release mechanism is pushing to main branch via `/release`.

## Motivation

These CI files add maintenance overhead (Dependabot PRs, workflow breakage on runner changes) without any deployment or publishing benefit. Removing them simplifies the repo — local `make test-ci` and `make lint` cover the same checks without the CI overhead.

## Rough Scope

- Delete `.github/workflows/ci.yml`
- Delete `.github/workflows/release-provenance.yml`
- Delete `.github/dependabot.yml`
- Remove `.github/` directory
- Keep Makefile CI targets (`test-ci`, `test-unit`) — they're useful locally