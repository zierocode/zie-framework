---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safety-check-redos-test.md
---

# Safety Check — Performance Contract Test for Very Long Commands (ReDoS Surface) — Design Spec

**Problem:** `safety-check.py` applies 22 regex patterns to arbitrary bash commands with no length limit and no existing test asserting a completion-time bound for very long or adversarially crafted inputs.

**Approach:** Add a test class `TestSafetyCheckPerformance` to `test_hooks_safety_check.py`. Each test runs the hook via subprocess with a large input and asserts that it completes within a tight wall-clock timeout (e.g. 2 seconds). The test uses Python's `time.time()` around the `subprocess.run` call — NOT `subprocess.run(timeout=...)` alone, because the subprocess timeout raises an exception rather than allowing a clean assertion. The goal is to document the performance contract and catch future ReDoS regressions from pattern changes.

**Components:**
- `tests/unit/test_hooks_safety_check.py` — new class `TestSafetyCheckPerformance`
- `hooks/safety-check.py` — BLOCKS and WARNS pattern lists (read-only reference)

**Data Flow — test cases to add:**

1. `test_very_long_safe_command_completes_quickly`:
   - Input: `"git status " + "a" * 100_000` (100k-char safe command, no patterns match).
   - Assert `returncode == 0`.
   - Assert wall-clock elapsed < 2.0 seconds.

2. `test_very_long_blocked_prefix_completes_quickly`:
   - Input: `"rm -rf / " + "x" * 100_000` (triggers BLOCKS pattern on first few chars, rest is noise).
   - Assert `returncode == 2` and `"BLOCKED" in stdout`.
   - Assert wall-clock elapsed < 2.0 seconds.

3. `test_adversarial_rm_rf_pattern_completes_quickly`:
   - Input: `"rm -rf " + " " * 50_000 + "/"` (spaces between `rm -rf` and `/` — tests `\s+` quantifier with large input).
   - Assert completes < 2.0 seconds (may block or pass depending on regex — document the result).

4. `test_adversarial_drop_database_pattern_completes_quickly`:
   - Input: `"drop" + " " * 50_000 + "database mydb"` (large whitespace between keywords — tests `\s+` in `\bdrop\s+database\b`).
   - Assert completes < 2.0 seconds.

5. `test_empty_command_completes_quickly`:
   - Input: `""` (edge case: empty command exits early at line 17 of safety-check.py).
   - Assert `returncode == 0` and elapsed < 0.5 seconds.

**Edge Cases:**
- The 2.0-second threshold is deliberately generous to avoid flakiness on slow CI machines. If a pattern causes catastrophic backtracking, it will take orders of magnitude longer (seconds to minutes), making the threshold easy to distinguish.
- `cmd = command.strip().lower()` is applied before regex matching — the `.lower()` call itself is O(n) on the full command string and is acceptable for 100k chars.
- All current BLOCKS patterns use `\s+` (one-or-more), not `\s*` (zero-or-more with nested quantifiers), so catastrophic backtracking risk is low — these tests are a regression guard, not a known-failing scenario.
- The `subprocess.run(timeout=...)` parameter must be set to 10 seconds as a hard kill, with the 2-second wall-clock check as the assertion — this prevents hanging the test suite if a future pattern does cause backtracking.

**Out of Scope:**
- Fixing existing patterns for ReDoS (current patterns are not vulnerable; this is preventive).
- Adding command length limits to `safety-check.py` (not required given current pattern shapes).
- Fuzzing the full 22-pattern set (out of scope for unit tests).
