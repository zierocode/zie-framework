---
approved: true
approved_at: 2026-03-22
backlog: backlog/zie-status-test-health.md
---

# zie-status Test Health Detection — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Make step 4 of /zie-status detect real test health from `.pytest_cache` instead of always reporting "? stale".

**Architecture:** The fix is purely in the `commands/zie-status.md` command file — update the step 4 prose to describe the exact detection logic (cache file existence, content emptiness, and mtime comparison). No Python hook changes required; the command instructs the agent reading it at runtime.

**Tech Stack:** Markdown command files, pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/zie-status.md` | Update step 4 with real detection logic |
| Modify | `tests/unit/test_sdlc_gates.py` | Add `TestZieStatusHealth` class |

---

## Task 1: Write failing tests (RED)

Add class `TestZieStatusHealth` to `tests/unit/test_sdlc_gates.py`.

The tests assert that `commands/zie-status.md` step 4 contains the real detection logic. All three tests must FAIL before the implementation step because the current step 4 only says "get last run timestamp" without specifying the cache path or the empty/non-empty distinction.

```python
class TestZieStatusHealth:
    def test_status_checks_lastfailed_file(self):
        content = read("commands/zie-status.md")
        assert ".pytest_cache/v/cache/lastfailed" in content, \
            "/zie-status step 4 must check .pytest_cache/v/cache/lastfailed"

    def test_status_detects_fail_on_nonempty_lastfailed(self):
        content = read("commands/zie-status.md")
        assert "non-empty" in content or "nonempty" in content or "not empty" in content, \
            "/zie-status step 4 must treat non-empty lastfailed as fail (✗)"

    def test_status_detects_pass_on_empty_lastfailed(self):
        content = read("commands/zie-status.md")
        assert "empty" in content and ("pass" in content.lower() or "✓" in content), \
            "/zie-status step 4 must treat empty lastfailed as pass (✓)"

    def test_status_detects_stale_on_no_cache(self):
        content = read("commands/zie-status.md")
        assert "no .pytest_cache" in content or "no cache" in content.lower() \
            or ".pytest_cache/` at all" in content or "no `.pytest_cache" in content, \
            "/zie-status step 4 must report ? stale when .pytest_cache is absent"

    def test_status_detects_stale_on_newer_test_files(self):
        content = read("commands/zie-status.md")
        assert "mtime" in content or "modified" in content.lower() or "newer" in content, \
            "/zie-status step 4 must compare mtime of cache vs test files"
```

Run: `make test-unit` — all 5 tests in `TestZieStatusHealth` must fail.

---

## Task 2: Implement (GREEN)

Replace step 4 in `commands/zie-status.md` with the following precise logic block:

```markdown
4. **Check test health**:
   - Check `.pytest_cache/v/cache/lastfailed`:
     - File exists and is **non-empty** (contains failed node IDs) → report `✗ fail`
     - File exists and is **empty** (last run had zero failures) → report `✓ pass`
     - If no `.pytest_cache/` directory at all → report `? stale`
   - Compare mtime of `.pytest_cache/` directory vs the newest file under `tests/`:
     - If any test file was modified more recently than `.pytest_cache/` → report `? stale`
     (A stale result overrides a prior pass/fail — if tests changed since the last run, the cached result is unreliable.)
```

Run: `make test-unit` — all 5 tests in `TestZieStatusHealth` must now pass.

---

## Task 3: Full suite

Run the full test suite to confirm no regressions:

```bash
make test-unit
```

Expected: all existing classes (`TestZieInitBacklog`, `TestZieShipMemory`, `TestZieRetroMemory`, `TestIntentDetectPlan`, `TestZieBuildGates`, `TestZiePlanCommand`, `TestZieIdeaBacklogFirst`, `TestROADMAPReadyLane`) continue to pass alongside the new `TestZieStatusHealth`.

If `make test` is available, run that too.

---

## Context from brain

_No prior memories on this feature. First implementation._
