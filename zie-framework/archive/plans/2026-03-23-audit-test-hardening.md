---
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-test-hardening.md
spec: specs/2026-03-23-audit-test-hardening-design.md
---

# Plan: Test Hardening

**Spec:** specs/2026-03-23-audit-test-hardening-design.md
**Effort:** M
**Test runner:** pytest

## Tasks

### Task 1 — autouse /tmp teardown fixtures in test_hooks_auto_test.py

**RED:** Write an `autouse=True` fixture inside `TestAutoTestDebounce` and
`TestAutoTestRunnerSelection` that yields and then deletes
`/tmp/zie-framework-last-test`. Run existing tests — they pass but the fixture
is not yet wired (tests currently leave stale state).

**GREEN:** Add the fixture to both classes:

```python
@pytest.fixture(autouse=True)
def _cleanup_debounce(self):
    yield
    p = Path("/tmp/zie-framework-last-test")
    if p.exists():
        p.unlink()
```

Remove any ad-hoc `if debounce.exists(): ...` cleanup scattered inside test
bodies.

**REFACTOR:** Confirm no `os.utime` workaround remains inside
`test_unknown_test_runner_exits_zero` — the fixture now guarantees a clean
state so the manual mtime manipulation is no longer needed.

---

### Task 2 — autouse /tmp teardown fixture in test_hooks_wip_checkpoint.py

**RED:** Write an `autouse=True` fixture inside `TestWipCheckpointCounter` that
yields and then deletes `/tmp/zie-framework-edit-count`. Assert that after the
fixture runs, the counter file is absent. The module-level `reset_counter()`
helper is still called manually — this is the failing state we want to
eliminate.

**GREEN:** Add the fixture to `TestWipCheckpointCounter`:

```python
@pytest.fixture(autouse=True)
def _cleanup_counter(self):
    yield
    p = Path("/tmp/zie-framework-edit-count")
    if p.exists():
        p.unlink()
```

Remove all `reset_counter()` calls from individual test methods. Delete (or
keep but stop calling) the `reset_counter()` module-level function.

**REFACTOR:** Verify `test_no_crash_on_fifth_edit_with_bad_url` no longer needs
to pre-seed the counter with a raw `write_text("4")` call outside of teardown
— adjust so the pre-seed write happens inside the test body only, and teardown
still cleans it up.

---

### Task 3 — Strengthen intent-detect happy-path assertions to JSON parse

**RED:** Change the five assertions in `TestIntentDetectHappyPath` from
substring checks (`"/zie-fix" in r.stdout`) to:

```python
data = json.loads(r.stdout)
assert data["additionalContext"] == "/zie-fix"
```

Run — these will fail immediately if `r.stdout` is not valid JSON or if the
key name is wrong, which exposes any existing protocol mismatch.

**GREEN:** Confirm `intent-detect.py` already emits a JSON object with an
`additionalContext` key containing the command string (per the commit
`af28367`). All five tests should now pass with the stricter assertion.

**REFACTOR:** Extract a helper `_parse_command(r)` in the test class that does
`json.loads(r.stdout)["additionalContext"]` so each assertion reads as a single
line. Add a guard assertion `assert r.stdout.strip() != ""` before the parse
to produce a clear error when output is unexpectedly empty.

---

### Task 4 — Add TestIntentDetectSkipGuards (frontmatter + long-message)

**RED:** Add a new class `TestIntentDetectSkipGuards` with two tests:

```python
def test_frontmatter_prompt_produces_empty_stdout(self, tmp_path):
    cwd = make_cwd_with_zf(tmp_path)
    r = run_hook({"prompt": "---\ntitle: My Note\n---\nsome content"}, tmp_cwd=cwd)
    assert r.stdout.strip() == ""

def test_long_message_produces_empty_stdout(self, tmp_path):
    cwd = make_cwd_with_zf(tmp_path)
    r = run_hook({"prompt": "x" * 501}, tmp_cwd=cwd)
    assert r.stdout.strip() == ""
```

Run — these may pass already if the guards exist in the hook, or fail if they
are absent/broken.

**GREEN:** If either test fails, locate the guard logic in `intent-detect.py`
and verify the conditions: `message.startswith("---")` and
`len(message) > 500`. Fix if needed (no source change expected — this is
behavioral verification).

**REFACTOR:** Add a boundary test for exactly 500 characters (should NOT be
suppressed) to confirm the `>` vs `>=` boundary is correct:

```python
def test_500_char_message_not_suppressed(self, tmp_path):
    cwd = make_cwd_with_zf(tmp_path)
    r = run_hook({"prompt": "fix the bug " + "x" * 488}, tmp_cwd=cwd)
    # 500 chars total with intent keywords — should produce output
    assert r.stdout.strip() != ""
```

---

### Task 5 — Add TestFindMatchingTest (direct unit tests, no subprocess)

**RED:** Add a new class `TestFindMatchingTest`. Import `find_matching_test`
directly via `importlib` or `sys.path` injection since the function is defined
inside `auto-test.py` at module scope:

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("auto_test", HOOK)
# Note: auto-test.py executes hook logic at import time — isolate with
# CLAUDE_CWD pointing to an empty tmp dir and non-Edit stdin to short-circuit
```

Write three tests:

1. A matching `test_{stem}.py` exists recursively under `tests/` — returns its
   path.
2. No matching file exists anywhere — returns `None`.
3. `runner="vitest"` with a `.test.ts` candidate in the same directory —
   returns its path.

These tests will fail until the import strategy is validated.

**GREEN:** Establish a safe import pattern. Since `auto-test.py` runs hook
logic at the top level on import, the cleanest approach is to redirect stdin to
an invalid JSON string before importing (the hook catches `Exception` and calls
`sys.exit(0)`, but that aborts import). Instead, refactor the top-level
execution guard minimally:

Wrap the top-level hook body in `if __name__ == "__main__" or
_HOOK_RUNNING:` — or, per the spec's out-of-scope constraint, use
`subprocess` with `--collect-only` plus a monkey-patch approach.

Preferred approach (minimal source change allowed by spec): add a single
`if __name__ == "__main__":` guard around the execution block at the bottom of
`auto-test.py`, leaving `find_matching_test` at module scope. Then import
cleanly.

**REFACTOR:** Once import works, ensure tests are parametrized where patterns
repeat. Add a fixture that creates the `tests/unit/` subdirectory structure
expected by the recursive search.

---

### Task 6 — Add TestWipCheckpointRoadmapEdgeCases

**RED:** Add a new class `TestWipCheckpointRoadmapEdgeCases` with three tests,
all using a fake API key and unreachable URL to exercise ROADMAP parsing
without a real network call:

```python
def test_missing_roadmap_no_crash(self, tmp_path): ...
    # zie-framework/ dir exists but ROADMAP.md absent
    # assert r.returncode == 0 and r.stdout.strip() == ""

def test_empty_now_section_no_checkpoint(self, tmp_path): ...
    # ROADMAP.md with "## Now\n" and no list items
    # assert checkpoint is not triggered (counter stays below 5 or stdout empty)

def test_malformed_now_items_graceful_skip(self, tmp_path): ...
    # ROADMAP.md with "## Now\nnot a list item\nanother line"
    # assert r.returncode == 0
```

Run — missing ROADMAP likely passes; empty/malformed cases may expose parsing
crashes.

**GREEN:** Inspect `wip-checkpoint.py` ROADMAP parsing logic. Add guards for:
- `ROADMAP.md` not present (already guarded likely, confirm)
- `## Now` section present but empty (no `- [ ]` lines)
- Non-list content under `## Now`

Fix any unguarded path.

**REFACTOR:** Consolidate the `autouse` teardown from Task 2 so
`TestWipCheckpointRoadmapEdgeCases` also inherits it (or add its own). These
tests should also clean up `/tmp/zie-framework-edit-count` since the counter
may increment during the five-edit path.

---

### Task 7 — Add TestAutoTestDebounceBoundary

**RED:** Add a new class `TestAutoTestDebounceBoundary` with two tests:

```python
def test_debounce_zero_always_runs(self, tmp_path): ...
    # config: {"test_runner": "pytest", "auto_test_debounce_ms": 0}
    # Write a fresh debounce file (mtime=now)
    # assert hook is NOT suppressed (elapsed >= 0ms always satisfies < 0ms? No — 0ms window means skip when elapsed < 0, which never happens)
    # assert "[zie-framework] Tests" in r.stdout OR r.returncode == 0 without suppression

def test_debounce_large_value_suppresses(self, tmp_path): ...
    # config: {"test_runner": "pytest", "auto_test_debounce_ms": 999999}
    # Write debounce file with mtime=now
    # assert hook exits silently (suppressed)
    # assert "[zie-framework] Tests" not in r.stdout
```

Include an `autouse=True` fixture in this class for `/tmp/zie-framework-last-test`.

**GREEN:** Confirm the debounce condition in `auto-test.py`:
`(time.time() - last_run) < (debounce_ms / 1000)`. With `debounce_ms=0`, the
window is 0 seconds — elapsed is always >= 0, so condition is always False and
hook runs. With `debounce_ms=999999`, window is ~277 hours — always suppressed
if debounce file was just written. Both behaviors should match without code
changes.

**REFACTOR:** Add a parametrized form if the two tests share substantial setup.
Ensure the `pytest` invocation in the `debounce_zero` test targets a file that
actually exists (or mock the subprocess call) so the test doesn't fail on
test-not-found rather than the debounce logic under test.
