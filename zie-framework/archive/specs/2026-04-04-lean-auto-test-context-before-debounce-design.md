---
approved: true
approved_at: "2026-04-04"
---

# Lean auto-test additionalContext — Design Spec

**Problem:** `auto-test.py` always emits `additionalContext` JSON (including
"No test file found...") even when the debounce guard will skip the test run,
burning live tokens on turns where no action will be taken.

**Approach:** Move the `additionalContext` print to after both the debounce
check and the test-file check. Only emit context when a matching test file is
found and the debounce window has passed. Suppress context entirely for the
"no test file" case — the "no test" signal is only useful when the user should
act on it, which is never immediately required.

**Components:**
- `hooks/auto-test.py` — single-file change: reorder the `additionalContext`
  print to after the debounce and test-file guard

**Data Flow:**
1. Hook receives PostToolUse Edit/Write event
2. Early exits: tool_name check, file_path check, zf-dir check, test_runner
   check, skip-extension check, cwd-boundary check (unchanged)
3. Debounce check → `sys.exit(0)` if within window (unchanged)
4. Write debounce timestamp (unchanged)
5. Call `find_matching_test()` — result cached in `matching_test` (unchanged)
6. **NEW gate:** if `matching_test` is None → `sys.exit(0)` (no context,
   no test run for the no-match case when debounce has passed)
7. **NEW position:** emit `additionalContext` with `"Affected test: <path>"`
   only when `matching_test` is not None
8. Build and run test command using `matching_test` (unchanged)

**Edge Cases:**
- `matching_test is None` + debounce cleared: previously ran `pytest tests/`
  broadly; this fallback is removed. Tests still run via `make test-unit`.
  The "no test file" case was already noisy context and a broad test run
  on every unmatched edit — both are eliminated.
- Debounce active: hook exits before additionalContext (unchanged behavior
  for debounced turns).
- `matching_test` found but test command fails: context was already emitted
  before the run — no change in failure path.

**Out of Scope:**
- Changing when the debounce timestamp is written.
- Any changes to `find_matching_test()` logic.
- vitest/jest runner paths (same logic applies but not specifically tested here).
