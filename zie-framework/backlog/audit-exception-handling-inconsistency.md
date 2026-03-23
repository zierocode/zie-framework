# Inconsistent exception handling strategy across hooks

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

Hooks use at least three different error patterns:
1. `except Exception:` — silent exit (auto-test.py:49)
2. `except Exception as e: print(e, file=stderr)` — noisy (session-learn.py:64)
3. Mixed approaches within same file (wip-checkpoint.py:40,81)

No consistent rule for when to log vs. stay silent. Debugging hook failures
requires reading source to know which pattern any given exception follows.

## Motivation

Establish a convention: outer guard (hook-level) stays silent to avoid blocking
Claude; inner operations log to stderr on failure. Document the convention in
`utils.py` or CLAUDE.md.
