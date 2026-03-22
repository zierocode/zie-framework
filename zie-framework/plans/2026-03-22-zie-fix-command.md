---
approved: true
approved_at: 2026-03-22
backlog: backlog/zie-fix-command.md
---

# /zie-fix Enhancement — Batch Recall + Domain Memory — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Upgrade `/zie-fix` memory integration from a single free-text recall to a batch domain-aware recall, and upgrade the write pattern to store root cause, fix, and recurrence classification with proper domain tags.

**Architecture:** The command file `commands/zie-fix.md` is the sole artifact to modify — no hook changes or new files needed. The recall call gains `project=`, `domain=`, and `tags=[bug, build-learning]` parameters with `limit=10`, replacing the bare `recall "<text>"` call. The remember call gains a structured prose format and replaces the generic `[bug, fix, <module-slug>]` tagset with `[bug, <project>, <domain>]`.

**Tech Stack:** Markdown command files, pytest

---

## Context from brain

<!-- zie-memory recall results would be surfaced here by /zie-plan before handing off to /zie-build -->

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `tests/unit/test_sdlc_gates.py` | Add `TestZieFixMemory` class — failing tests (RED) |
| Modify | `commands/zie-fix.md` | Upgrade recall + remember calls to spec pattern (GREEN) |

---

## Task 1: Write failing tests for zie-fix memory integration (RED)

**Files:**

- Modify: `tests/unit/test_sdlc_gates.py`

- [ ] **Step 1: Add `TestZieFixMemory` class with failing assertions**

```python
class TestZieFixMemory:
    def test_fix_uses_batch_recall_with_domain(self):
        content = read("commands/zie-fix.md")
        assert "domain" in content and "tags=[bug" in content, \
            "/zie-fix must use batch recall with domain= and tags=[bug, ...]"

    def test_fix_recall_has_limit(self):
        content = read("commands/zie-fix.md")
        assert "limit=10" in content, \
            "/zie-fix recall must set limit=10 for batch query"

    def test_fix_stores_root_cause_and_pattern(self):
        content = read("commands/zie-fix.md")
        assert "root cause" in content.lower() and "pattern" in content.lower(), \
            "/zie-fix must store root cause and recurring/one-off pattern in remember call"

    def test_fix_remember_tags_use_domain_not_module_slug(self):
        content = read("commands/zie-fix.md")
        assert "tags=[bug, <project>, <domain>]" in content, \
            "/zie-fix remember must use tags=[bug, <project>, <domain>] not module-slug"
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieFixMemory -v
```

All four tests must FAIL before proceeding to Task 2.

---

## Task 2: Implement zie-fix memory enhancement (GREEN)

**Files:**

- Modify: `commands/zie-fix.md`

- [ ] **Step 1: Replace the Pre-flight recall call**

Current (line ~15):

```text
recall "<bug description>"
```

Target:

```text
recall project=<project> domain=<domain> tags=[bug, build-learning] limit=10
→ detect recurring patterns, surface known fragile areas
```

- [ ] **Step 2: Replace the Phase 5 remember call**

Current (line ~56):

```text
remember "Bug: <description>. Root cause: <cause>. Fix: <approach>. Regression test: <test name>." priority=auto tags=[bug, fix, <module-slug>] project=<project>
```

Target:

```text
remember "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]
```

- [ ] **Step 3: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieFixMemory -v
```

All four tests must PASS.

- [ ] **Step 4: Run full test suite to confirm no regressions**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py -v
```

---

## Task 3: Refactor + verify (REFACTOR)

- [ ] **Step 1: Review updated `commands/zie-fix.md` for clarity**
  - Confirm Pre-flight section reads naturally with the new batch recall.
  - Confirm Phase 5 note prints `Pattern: recurring|one-off` in the summary block.
  - Confirm no leftover references to `<module-slug>` or bare `recall "..."` pattern.

- [ ] **Step 2: Update summary print block to include Pattern line**

The terminal summary printed at end of command should include:

```text
Bug fixed: <description>
Root cause: <cause>
Fix: <brief description>
Pattern: <recurring|one-off>
Regression test: <test name>

Run /zie-ship when ready to release.
```

- [ ] **Step 3: Final test run**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py -v
```

All tests pass — task complete.
