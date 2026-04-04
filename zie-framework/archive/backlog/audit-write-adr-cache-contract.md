# write_adr_cache return contract mismatch

**Severity**: High | **Source**: audit-2026-04-01

## Problem

`utils.write_adr_cache()` returns `bool` (True/False), but every command that
calls it — `zie-audit.md`, `zie-plan.md`, `zie-implement.md`, `zie-sprint.md`
— documents the return as a tuple `(True, adr_cache_path)` / `(False, None)`.

When Claude follows the command instructions and attempts to destructure the
return value, it either gets a `TypeError` or silently assigns `adr_cache_path`
from the wrong position, meaning context bundles downstream receive
`adr_cache_path = None` even on success.

## Motivation

Every command that uses the ADR cache for reviewer context silently degrades
when this contract bug is present. Fix: either change `write_adr_cache` to
return `(bool, path_or_none)` tuple, or update all 4 command docs to use the
bool return correctly.
