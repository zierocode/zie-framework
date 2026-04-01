---
slug: audit-write-adr-cache-contract
status: draft
date: 2026-04-01
---
# Plan: Fix write_adr_cache Return Contract

## Tasks

- [ ] Task 1: Write failing tests for tuple return in `test_adr_cache.py`
  Update `TestWriteAdrCache` — change all `assert result is True/False` assertions to
  assert `(bool, Path | None)` tuple. Specifically:
  - `test_returns_true_on_success` → assert `result == (True, <Path>)` and path exists
  - `test_returns_false_when_decisions_empty` → assert `result == (False, None)`
  - `test_returns_false_when_decisions_missing` → assert `result == (False, None)`
  - `test_returns_false_on_symlink` → assert `result == (False, None)`
  - `test_silently_returns_false_on_os_error` → assert `result == (False, None)`
  Also add one new test: `test_success_path_matches_expected_location` — confirm the
  returned `Path` equals `tmp_path / "zie-<safe_id>" / "adr-cache.json"`.
  Fix `test_hit_when_mtime_matches` in `TestGetCachedAdrs` — that test calls
  `write_adr_cache(...) is True`; update to unpack tuple before the `is True` check.
  Run `make test-fast` → expect RED on `TestWriteAdrCache` tests.

- [ ] Task 2: Update `write_adr_cache` in `hooks/utils.py` to return tuple
  - Change return type annotation: `-> bool` → `-> tuple[bool, Path | None]`
  - Update docstring: "Returns `(True, cache_path)` on success, `(False, None)` if
    decisions_dir is empty/missing or write fails."
  - On success path (after `safe_write_tmp` succeeds): return `(True, cache_path)`
    instead of the `safe_write_tmp` result.
  - On all early-exit / failure paths (`not adr_files`, `safe_write_tmp` returns falsy,
    outer `except`): return `(False, None)`.
  Run `make test-fast` → expect GREEN on `TestWriteAdrCache`, RED on `TestGetCachedAdrs`
  (the `test_hit_when_mtime_matches` unpacking fix from Task 1 may not cover all callers —
  verify here).

- [ ] Task 3: Update `commands/zie-implement.md` to show tuple destructure pattern
  The current line (line 46) reads:
  `Read decisions/*.md → write_adr_cache → adr_cache_path`
  Change to match the pattern used in `zie-plan.md` and `zie-sprint.md`:
  `Call write_adr_cache(session_id, adrs_content, "zie-framework/decisions/"):`
  `- Returns (True, adr_cache_path) → save path`
  `- Returns (False, None) → set adr_cache_path = None`
  Run `make test-fast` to verify no test regresses on `zie-implement.md` content.

- [ ] Task 4: Verify `zie-audit.md`, `zie-plan.md`, `zie-sprint.md` need no changes
  Grep each file for `write_adr_cache` return documentation and confirm they already
  show `(True, adr_cache_path)` / `(False, None)` tuple pattern. No edits required if
  confirmed. Document findings in a comment in this plan file (or simply mark as
  verified).

- [ ] Task 5: Run full test suite and confirm green
  Run `make test-ci`. Assert:
  - No test asserts a bare `bool` from `write_adr_cache` (Grep `is True\|is False` inside
    `TestWriteAdrCache` should return 0 matches after Task 1 changes).
  - All `TestWriteAdrCache` tests pass.
  - All `TestGetCachedAdrs` tests pass (callers updated in Task 1).
  - Command doc tests (`test_zie_implement_context_bundle.py`, etc.) pass.
  Coverage gate passes.

## Test Strategy

**Task 1 (RED):** Run `pytest tests/unit/test_adr_cache.py -x` — expect failures on
`TestWriteAdrCache` assertions because the implementation still returns `bool`.

**Task 2 (GREEN):** Run `pytest tests/unit/test_adr_cache.py` — all tests should pass.
Also run `pytest tests/unit/test_zie_implement_context_bundle.py` to confirm no
collateral breakage from the utils change.

**Task 3 (verify command doc):** Run `pytest tests/unit/test_zie_implement_context_bundle.py`
— confirm `test_context_bundle_references_write_adr_cache` still passes. If any test
checks for specific tuple-pattern prose in `zie-implement.md`, confirm it passes green.

**Task 4 (no-op verify):** `grep -n "write_adr_cache" commands/zie-{audit,plan,sprint}.md`
— confirm tuple doc already present. No test to write; this is a read-only audit step.

**Task 5 (CI gate):** `make test-ci` must pass with no failures and coverage ≥ threshold.
Final Grep sanity: `grep -n "is True\|is False" tests/unit/test_adr_cache.py` should show
no matches inside `TestWriteAdrCache` methods.

## Rollout

Tasks must run in order: Task 1 (tests, RED) → Task 2 (impl, GREEN) → Task 3 (docs) →
Task 4 (audit no-op) → Task 5 (full CI). No parallelism — each task depends on the
previous to ensure TDD RED/GREEN discipline is maintained.

Tasks 3 and 4 are independent of each other and could be done in parallel, but
sequencing them after Task 2 keeps the diff clean and avoids any intermediate state
where the command docs are inconsistent with a still-failing implementation.
