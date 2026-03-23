---
approved: true
approved_at: 2026-03-24
backlog: backlog/posttooluse-additionalcontext.md
---

# PostToolUse additionalContext Test File Hints — Design Spec

**Problem:** After every Write/Edit, Claude must spend an extra Glob or Read tool
call to discover which test file covers the changed code, wasting a full lookup
turn per TDD cycle.

**Approach:** Extend `hooks/auto-test.py` to emit a `hookSpecificOutput`
JSON block on stdout after every Write/Edit tool event, injecting an
`additionalContext` string that names the matched test file (or prompts Claude
to write one). The `find_matching_test()` function already performs the lookup;
this change surfaces its result directly into Claude's context rather than only
using it to build the test command. All existing debounce, execution, and
safety behaviors remain unchanged — the context injection happens regardless of
whether the debounce suppresses a test run.

**Components:**

- `hooks/auto-test.py` — primary change: emit `hookSpecificOutput.additionalContext` JSON to stdout after resolving test match
- `tests/unit/test_auto_test.py` — new/extended tests: context injected when match found, context injected with "write one" message when no match, no regression on existing test-run behavior, debounce suppression does not suppress context injection

**Data Flow:**

1. PostToolUse event fires; `read_event()` parses stdin JSON.
2. Early-exit guards run: tool_name not in (`Edit`, `Write`), missing `file_path`, missing `zie-framework/` dir, missing `test_runner` config — all still exit 0 silently as today.
3. `changed = Path(file_path).resolve()` — resolve the edited file path.
4. `matching_test = find_matching_test(changed, test_runner, cwd)` — reuse existing logic; returns absolute path string or `None`.
5. Build `additional_context` string:
   - Match found: `"Affected test: {matching_test}"` (absolute path)
   - No match: `"No test file found for {changed.name} — write one"`
6. Emit to stdout:
   ```json
   {"hookSpecificOutput": {"additionalContext": "<additional_context string>"}}
   ```
7. Continue into debounce check. If debounced, exit 0 (no test run, but context was already emitted in step 6).
8. If not debounced, run test subprocess as today; print pass/fail/timeout messages as today.

**Edge Cases:**

- **Debounce active:** Context injection (step 6) must occur before the debounce check (step 7) so Claude always receives the hint, even when the test run itself is skipped.
- **No test_runner configured:** Exit 0 before step 4 — no context emitted. Behavior unchanged from today.
- **file_path outside cwd:** The `is_relative_to` guard currently exits early after debounce. Move `find_matching_test` call and context emission to before this guard so out-of-cwd edits still get a context hint if a matching test exists. Alternatively, apply the same guard to context emission to keep logic consistent — preferred for simplicity: guard applies to both, exit 0 on out-of-cwd.
- **vitest/jest runners:** `find_matching_test` supports these runners; context emission is runner-agnostic and works for all three (`pytest`, `vitest`, `jest`).
- **`find_matching_test` raises OSError:** Already guarded inside the function with `try/except OSError: pass`; returns `None` on failure — triggers "write one" message.
- **Stdout conflict:** The existing hook prints plain-text pass/fail lines to stdout. The `hookSpecificOutput` JSON must be emitted as its own `print()` call on a separate line so Claude Code can parse it independently. Emit it before subprocess output, not interleaved.
- **Multiple rapid edits:** Debounce prevents repeated test runs; context injection fires every time regardless (each edit may touch a different file, so the hint is always fresh).
- **Non-Python test runners (vitest/jest) with missing `__tests__` dir:** `c.exists()` calls inside `find_matching_test` return False silently — falls through to `None` — triggers "write one" message. No crash.

**Out of Scope:**

- Changing the `find_matching_test()` algorithm or expanding its heuristics (e.g., fuzzy matching, import-graph analysis).
- Emitting `additionalContext` for hooks other than `auto-test.py`.
- Surfacing test results (pass/fail counts) inside `additionalContext` — that remains in plain stdout messages.
- Any changes to `hooks.json` event bindings — hook already fires on `PostToolUse:Write/Edit`.
- Supporting test runners beyond the three already handled (`pytest`, `vitest`, `jest`).
- Persisting the test file hint to `zie-memory` or any tmp file.
