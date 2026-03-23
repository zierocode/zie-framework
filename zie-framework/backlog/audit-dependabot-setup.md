# No Dependabot for development dependencies

**Severity**: Medium | **Source**: audit-2026-03-24 (OpenSSF Scorecard)

## Problem

pytest and other dev dependencies have no automated update monitoring. OpenSSF
Scorecard's `Dependency-Update-Tool` check fails without Dependabot or Renovate
configured. Dev deps can accumulate CVEs silently.

## Motivation

A simple `.github/dependabot.yml` watching `pip` and `github-actions` ecosystems
satisfies OpenSSF, provides automatic PRs for security patches, and costs nothing
to maintain. Required for OpenSSF badge candidacy.
