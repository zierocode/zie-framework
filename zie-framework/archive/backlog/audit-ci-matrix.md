# CI tests only ubuntu-latest + Python 3.13 — no macOS, no Python 3.11

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`ci.yml` runs a single job on `ubuntu-latest` with `python-version-file:
.python-version` (Python 3.13). No matrix strategy is defined.

Claude Code's primary user platform is macOS. `hooks/utils.py` uses
`str | None` union syntax (Python 3.10+). Subprocess behavior (SIGTERM,
`/tmp` path semantics) differs between macOS and Linux. A bug affecting
Python 3.11 or macOS would not be caught in CI.

## Motivation

Add a GitHub Actions matrix with at minimum `macos-latest` + `python: 3.11`
alongside the existing `ubuntu-latest` + `3.13` job.
