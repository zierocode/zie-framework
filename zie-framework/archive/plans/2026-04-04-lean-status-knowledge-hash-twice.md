---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-status-knowledge-hash-twice.md
---

# Lean Status: Deduplicate knowledge-hash computation — Implementation Plan

**Goal:** Eliminate the redundant second `python3 hooks/knowledge-hash.py` subprocess in Step 4 of `/status` by having Step 4 reference the already-injected bang output instead of recomputing it.
**Architecture:** Two-part change in `commands/status.md`: (1) add a binding label to the existing bang-injection block so the in-context output is named `knowledge_hash_current`, and (2) rewrite Step 4 to reference `knowledge_hash_current` rather than invoking a new Bash subprocess. A new test assertion in `tests/unit/test_zie_status_drift.py` locks this in by asserting the standalone `python3 hooks/knowledge-hash.py` call does not appear in Step 4.
**Tech Stack:** Markdown (commands spec), Python (pytest unit tests)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/status.md` | Label bang-injection output + rewrite Step 4 to use the binding instead of a second subprocess |
| Modify | `tests/unit/test_zie_status_drift.py` | Add assertion: explicit `python3 hooks/knowledge-hash.py` does not appear in Step 4 body |

## Task Sizing

S plan — 2 tasks, one session. Task 1 adds the failing test assertion (RED); Task 2 makes the production change to `status.md` (GREEN). Task 2 depends on Task 1.

---

## Task 1: Add failing test for no explicit hash call in Step 4

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_zie_status_drift.py` has a new test `test_no_explicit_hash_call_in_step4` that fails because `commands/status.md` currently contains `python3 hooks/knowledge-hash.py` in Step 4
- Existing tests in the file still pass
- `make test-unit` shows exactly one new failure

**Files:**
- Modify: `tests/unit/test_zie_status_drift.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_zie_status_drift.py`:
  ```python
  def test_no_explicit_hash_call_in_step4():
      """Step 4 must NOT spawn a second knowledge-hash.py subprocess.
      The bang injection at command load is the only execution.
      """
      text = CMD.read_text()
      # Find the Step 4 section (between "4. **Check knowledge drift**" and the next top-level step)
      step4_start = text.find("4. **Check knowledge drift**")
      assert step4_start != -1, "Step 4 not found in status.md"
      # Find next numbered step after Step 4
      step5_start = text.find("5. **Check test health**", step4_start)
      assert step5_start != -1, "Step 5 not found after Step 4"
      step4_body = text[step4_start:step5_start]
      assert "python3 hooks/knowledge-hash.py" not in step4_body, (
          "Step 4 must not spawn a second knowledge-hash.py subprocess — "
          "use the bang-injected knowledge_hash_current binding instead"
      )
  ```

  Run: `make test-unit` — must FAIL with:
  ```
  FAILED tests/unit/test_zie_status_drift.py::test_no_explicit_hash_call_in_step4
  AssertionError: Step 4 must not spawn a second knowledge-hash.py subprocess
  ```

- [ ] **Step 2: Implement (GREEN)**
  No implementation in this task — GREEN comes from Task 2.

- [ ] **Step 3: Refactor**
  No refactoring needed.
  Run: `make test-unit` — still FAIL on new test (expected)

---

## Task 2: Remove redundant hash subprocess from status.md Step 4

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/status.md` bang-injection block labels its output as `knowledge_hash_current`
- Step 4 references `knowledge_hash_current` (in-context binding) instead of calling `python3 hooks/knowledge-hash.py`
- `/status` output is identical — same Knowledge row, same sentinel handling
- `make test-unit` passes with no errors

**Files:**
- Modify: `commands/status.md`

- [ ] **Step 1: Write failing tests (RED)**
  Already RED from Task 1. Confirm:
  Run: `make test-unit` — must FAIL on `test_no_explicit_hash_call_in_step4`

- [ ] **Step 2: Implement (GREEN)**

  **Change 1:** Update the bang-injection block (lines 15–21) to label the output:

  ```markdown
  **Live context (injected at command load):**

  ROADMAP snapshot (first 30 lines):
  !`cat zie-framework/ROADMAP.md | head -30`

  Knowledge hash (stored as `knowledge_hash_current`):
  !`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`
  ```

  **Change 2:** Replace Step 4 body — remove the explicit `python3 hooks/knowledge-hash.py` bash block and replace with a reference to the in-context binding:

  ```markdown
  4. **Check knowledge drift** using `knowledge_hash_current` (already injected above — no second subprocess):

     - Read `knowledge_hash` from `zie-framework/.config`
     - If missing → Knowledge status: `? no baseline — run /resync`
     - Compare `knowledge_hash_current` to stored hash:
       - `knowledge_hash_current` equals `"knowledge-hash: unavailable"` → Knowledge status: `? unavailable`
       - Equal to stored hash → `✓ synced (<knowledge_synced_at>)`
       - Differs → `⚠ drift detected — run /resync`
     - Knowledge row is informational only — does not block suggestions
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No further cleanup needed — the change is minimal and complete.
  Run: `make test-unit` — still PASS
