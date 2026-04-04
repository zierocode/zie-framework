# Raise coverage gate from 43% toward community standard (70%)

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

Coverage gate frozen at 43% per ADR-027 (intentionally lowered from 50% due
to subprocess measurement challenges at the time). The `sitecustomize.py`
measurement infra is now stable and working. The codebase has grown to ~1,920
unit tests across 145 files, but the gate hasn't moved in 36 releases.

Community standard for Python hook-based tooling is 70–80%. At 43%, over half
the hook code (error paths, config branches, edge cases) is unverified by CI.

## Motivation

Incrementally raise `--fail-under` in the Makefile:
1. Measure current actual coverage (`make test-ci` output)
2. Set gate to current measured level (no new red)
3. Establish a ratchet: gate never decreases in a release
4. Target 70% over the next 3–4 sprints

Write a new ADR superseding ADR-027 documenting the ratchet policy.
