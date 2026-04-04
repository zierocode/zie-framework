# truncate-auto-test-output — Design Spec

**Problem:** `hooks/auto-test.py` (PostToolUse) runs pytest on every Edit/Write and emits the full test output into context, wasting tokens on large test suites and on non-code file edits where tests are irrelevant.

**Approach:** Add a `truncate_test_output(raw: str) -> str` helper inside `auto-test.py` that reduces pytest output to: (1) the pass/fail summary line (e.g. `5 passed`, `1 failed, 4 passed`) and (2) the first `FAILED` block only (from `FAILED ...` header through the next blank separator or end-of-output). Additionally, gate the entire hook on file extension — skip test execution silently for known non-code file types: `*.md`, `*.json`, `*.yaml`, `*.yml`, `*.toml`, `*.cfg`, `*.ini`, `*.txt`. Both paths — `auto_test_max_wait_s > 0` (Popen) and fallback `subprocess.run` — use the same truncation helper.

**Components:**
- `hooks/auto-test.py` — add `truncate_test_output()` function, add extension skip guard, apply truncation to both output paths
- `tests/unit/test_hooks_auto_test.py` — add unit tests for `truncate_test_output()` and the extension skip guard

**Data Flow:**

1. PostToolUse event arrives — tool_name checked (Edit/Write only, existing guard).
2. NEW: Check `changed.suffix` against skip-list (`{".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"}`). If match → `sys.exit(0)` silently (no output, no debounce write).
3. Existing: additionalContext injection, debounce check, test command build — unchanged.
4. Existing: subprocess runs pytest, captures stdout+stderr.
5. NEW: On non-zero exit, pass `stdout_data + stderr_data` through `truncate_test_output()` before printing. On zero exit, print the existing `Tests pass ✓` line unchanged.
6. `truncate_test_output(raw)` algorithm:
   - Find summary line: last non-empty line matching `r'\d+\s+(passed|failed|error|skipped|xfailed|xpassed)'` (pytest always prints this last; pattern covers mixed combos like `5 passed, 2 skipped` because any such line contains at least one matching keyword).
   - Find first FAILED block: lines from first line matching `^(FAILED|E   |_ )` through the next blank line or `=====` separator.
   - Return: `[zie-framework] Tests FAILED — fix before continuing\n<summary_line>\n\n<first_failure_block>` (capped at 30 lines total).
   - If no FAILED block found (e.g. parse miss): fall back to first 10 non-empty lines.

**Edge Cases:**
- All tests pass → no truncation applied, existing `Tests pass ✓` message emitted unchanged.
- No FAILED block parseable (unusual output format) → fallback: first 10 non-empty lines of raw output.
- File extension is uppercase (`.MD`, `.JSON`) → normalise with `.lower()` before checking skip-list.
- `changed.suffix` is empty (no extension, e.g. `Makefile`) → not in skip-list → hook proceeds normally.
- vitest/jest output formats → `truncate_test_output` is runner-agnostic: summary-last + first-failure block logic degrades gracefully (shows first 10 lines fallback for non-pytest formats).
- Timeout path → timeout message is already minimal; truncation not applied (timeout exits before output collection).
- Debounce suppression → skip-list check happens BEFORE debounce write, so skipped files do not reset the debounce clock.

**Out of Scope:**
- Changing pytest flags (`--tb`, `--no-header`, etc.) — existing flags are unchanged.
- Configurable skip-list via `.config` — hardcoded set is sufficient; can be extended later if needed.
- Truncation of the `additionalContext` injection line — that line is already minimal.
- vitest/jest runner-specific output parsing — fallback covers these runners adequately.
- Streaming/line-by-line truncation — full buffer is already collected before printing.
