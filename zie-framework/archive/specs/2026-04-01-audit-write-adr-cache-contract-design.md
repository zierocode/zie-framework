---
slug: audit-write-adr-cache-contract
status: draft
date: 2026-04-01
---

# Spec: Fix write_adr_cache Return Contract

## Problem

`utils.write_adr_cache()` is documented and implemented to return `bool`
(`True` on success, `False` on failure). However, all four commands that call
it — `zie-audit.md`, `zie-plan.md`, `zie-implement.md`, and `zie-sprint.md`
— document the return value as a tuple `(True, adr_cache_path)` /
`(False, None)`.

When Claude follows the command instructions and attempts to destructure the
return value as a tuple, it either gets a `TypeError` (tuple unpacking from
`bool`) or silently mis-assigns variables, causing `adr_cache_path` to be
`None` even on success. This means every command that passes `adr_cache_path`
into a reviewer context bundle silently degrades — reviewers receive no ADR
cache path despite a successful write.

The bug is a single-source contract mismatch: the implementation in `utils.py`
returns `bool`, but four downstream consumers expect a `(bool, path_or_None)`
tuple. The fix is to align the source of truth (the implementation) to the
expected interface, then update all consumers to match.

## Proposed Solution

**Option A (chosen):** Change `write_adr_cache` in `hooks/utils.py` to return
`tuple[bool, Path | None]` — `(True, cache_path)` on success,
`(False, None)` on failure. This is the single-source fix. All four command
docs already document the tuple contract, so updating the implementation makes
the docs correct without rewriting them.

Changes required:

1. **`hooks/utils.py`** — Update `write_adr_cache`:
   - Change return type annotation from `-> bool` to `-> tuple[bool, Path | None]`
   - Update docstring to reflect tuple return
   - On success: return `(True, cache_path)` instead of the result of `safe_write_tmp`
   - On all failure paths: return `(False, None)` instead of `False`

2. **`commands/zie-audit.md`** — No change needed (already documents tuple).

3. **`commands/zie-plan.md`** — No change needed (already documents tuple).

4. **`commands/zie-implement.md`** — Update inline prose to clarify tuple
   destructure pattern (currently omits the tuple pattern — just says
   `write_adr_cache → adr_cache_path` without showing destructure).

5. **`commands/zie-sprint.md`** — No change needed (already documents tuple).

6. **Tests** — Update any unit tests for `write_adr_cache` that assert a
   `bool` return to assert the `(bool, path_or_None)` tuple return instead.

## Acceptance Criteria

- [ ] `write_adr_cache` in `hooks/utils.py` returns `(True, Path)` on success
- [ ] `write_adr_cache` in `hooks/utils.py` returns `(False, None)` on all failure paths (no ADR files, write error, exception)
- [ ] Return type annotation is `tuple[bool, Path | None]`
- [ ] Docstring in `utils.py` documents the tuple return contract
- [ ] `commands/zie-implement.md` clearly shows the tuple destructure pattern (consistent with `zie-plan.md` and `zie-sprint.md`)
- [ ] All existing unit tests for `write_adr_cache` pass with the new return type
- [ ] No test asserts a bare `bool` return from `write_adr_cache`
- [ ] `make test-fast` passes green

## Out of Scope

- Changing `read_adr_cache` — it already returns `str | None`, which is correct
- Refactoring any other utils functions
- Changing how `adr_cache_path` is used inside the commands beyond the destructure pattern
- Adding new ADR cache features (expiry, versioning, etc.)
