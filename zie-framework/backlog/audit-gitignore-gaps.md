# .gitignore missing evidence/ and .pytest_cache entries

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`.gitignore` doesn't include `zie-framework/evidence/` or `.pytest_cache/`.
Audit reports written to `evidence/` would be accidentally committed (they may
contain sensitive project details). `.pytest_cache/` is a common noise directory
that should be gitignored.

## Motivation

Trivial XS fix. The `evidence/` gap is more important — audit data is local-only
by design and must not enter the repo history.
