# Duplicated urllib.request POST pattern across session-learn and wip-checkpoint

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`session-learn.py:48-65` and `wip-checkpoint.py:62-82` each contain an identical
implementation of JSON + Bearer token HTTP POST via `urllib.request`. If the API
contract changes (headers, timeout, error handling), both files must be updated
in sync — and they will inevitably diverge.

## Motivation

Extract a shared `call_zie_memory_api(url, key, payload)` helper in `utils.py`.
Reduces duplication from ~35 lines × 2 to ~10 lines shared.
