# Add Bandit/Semgrep SAST to CI pipeline

**Severity**: High | **Source**: audit-2026-03-24 (OpenSSF Scorecard requirement)

## Problem

No static analysis tool runs on this codebase. Hooks use subprocess, /tmp writes,
regex on untrusted input — all patterns Bandit flags. OpenSSF Scorecard's `SAST`
check fails without automated security scanning on every PR.

## Motivation

Bandit would have caught the safety-check bypass vectors and /tmp race conditions
earlier. Adding `bandit -r hooks/` to `make lint` and to pre-commit ensures
security regressions are caught before merge. Required for OpenSSF compliance.
