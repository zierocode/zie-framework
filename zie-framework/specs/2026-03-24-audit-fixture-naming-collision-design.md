---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-fixture-naming-collision.md
---

# Unique Fixture Names for _cleanup_debounce in test_hooks_auto_test.py — Design Spec

**Problem:** Three `autouse` fixtures named `_cleanup_debounce` exist in separate test classes within `test_hooks_auto_test.py` (lines 63, 120, 137), risking silent pytest fixture shadowing and incorrect debounce-file teardown.

**Approach:** Rename each fixture to a unique, descriptive name that reflects its owning class. No logic changes are needed — only the `def` name and the `@pytest.fixture` decorator reference. Since these are `autouse` fixtures scoped to their class, renaming is sufficient to eliminate shadowing; no `conftest.py` migration is required unless future cross-class sharing is needed.

**Components:**
- `tests/unit/test_hooks_auto_test.py` — three `_cleanup_debounce` fixture definitions at lines 63, 120, 137

**Data Flow:**
1. `TestAutoTestDebounce._cleanup_debounce` (line 63) → rename to `_cleanup_debounce_debounce`.
2. `TestAutoTestRunnerSelection._cleanup_debounce` (line 120) → rename to `_cleanup_debounce_runner`.
3. `TestAutoTestDebounceBoundary._cleanup_debounce` (line 137) → rename to `_cleanup_debounce_boundary`.
4. pytest collects fixtures per class scope — no test function references these by name (they are `autouse`), so no call-site changes are needed.
5. Run `make test-unit` to verify all three classes still have correct teardown (debounce files removed after each test).

**Edge Cases:**
- If pytest ever resolves `autouse` fixtures by name across scopes, duplicate names in the same module could cause one class's fixture to run for another class's tests — renaming eliminates this risk entirely.
- If a future refactor moves tests into a shared `conftest.py`, the fixtures should be merged into one parameterised fixture at that point.
- The `load_module` fixture in `TestFindMatchingTest` is not `autouse` and does not create debounce files — it is unaffected.

**Out of Scope:**
- Moving fixtures to `conftest.py` (not needed given current test organisation).
- Changing fixture logic or teardown behaviour.
- Other test files that may have similar naming patterns (separate audit item if found).
