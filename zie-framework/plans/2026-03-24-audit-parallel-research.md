---
approved: false
approved_at: ~
backlog: backlog/audit-parallel-research.md
spec: specs/2026-03-24-audit-parallel-research-design.md
---

# /zie-audit Parallel External Research — Implementation Plan

**Goal:** Change Phase 3 of `/zie-audit` from a sequential `for query in queries` loop to a single parallel WebSearch dispatch, reducing Phase 3 latency from ~45s to ~5s.
**Architecture:** Single file change — `commands/zie-audit.md` Phase 3 prose rewritten to (1) construct all queries first, (2) dispatch ALL WebSearch calls in one parallel batch, (3) collect results dict keyed by query, (4) synthesize identically to current behavior. WebFetch follow-ups remain sequential. Failed queries fall back to "Research unavailable".
**Tech Stack:** Markdown (command definition), pytest (Path.read_text() content assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-audit.md` | Replace Phase 3 sequential loop with parallel dispatch instruction |
| Create | `tests/unit/test_audit_parallel_research.py` | Assert parallel dispatch present, sequential loop absent from Phase 3, fallback phrase present |

---

## Task 1: Modify `commands/zie-audit.md` — Phase 3 parallel dispatch

<!-- depends_on: none -->

**Acceptance Criteria:**
- Phase 3 instructs dispatching all WebSearch calls in a single parallel batch
- Phase 3 does NOT contain a sequential `for query in queries` loop instruction
- Phase 3 contains the fallback phrase "Research unavailable" for failed queries
- WebFetch follow-up calls remain sequential (unchanged)
- Query construction logic is unchanged (still capped at 15 queries)

**Files:**
- Modify: `commands/zie-audit.md`
- Create: `tests/unit/test_audit_parallel_research.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_audit_parallel_research.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  def _phase3_text() -> str:
      """Extract the Phase 3 section from zie-audit.md."""
      text = (COMMANDS_DIR / "zie-audit.md").read_text()
      # Slice from Phase 3 header to Phase 4 header
      start = text.index("## Phase 3")
      end = text.index("## Phase 4", start)
      return text[start:end]


  class TestAuditParallelResearch:
      def test_parallel_dispatch_instruction_present(self):
          phase3 = _phase3_text()
          assert "parallel" in phase3.lower(), (
              "Phase 3 must instruct dispatching WebSearch calls in parallel"
          )

      def test_sequential_loop_instruction_absent(self):
          phase3 = _phase3_text()
          assert "for query in queries" not in phase3, (
              "Phase 3 must not contain a sequential 'for query in queries' loop instruction"
          )

      def test_research_unavailable_fallback_present(self):
          phase3 = _phase3_text()
          assert "Research unavailable" in phase3, (
              "Phase 3 must contain 'Research unavailable' fallback for failed queries"
          )
  ```
  Run: `make test-unit` — must FAIL (`for query in queries` present, parallel not present)

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md`, replace the Phase 3 execution block.

  Before (lines ~136–139):
  ```
  Run `WebSearch` for each query (cap at 15 queries to keep latency manageable).
  Use `WebFetch` for high-value results to read the full document.

  If a query fails → skip gracefully, note "Research unavailable for this query"
  in the report section.
  ```

  After:
  ```
  Cap the query list at 15 entries. Then dispatch **all** WebSearch calls in a
  single parallel batch — do not loop sequentially. Collect results into a dict
  keyed by query string.

  If any individual query fails → record "Research unavailable" for that query
  and continue; do not abort the batch.

  After the parallel batch completes, use `WebFetch` sequentially for any
  high-value URLs returned by the search results (WebFetch depends on search
  output so it remains sequential).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Re-read the full Phase 3 section to confirm:
  - Query construction block (`queries = []` ... `queries +=` lines) is
    identical to before — no changes to construction logic or 15-query cap.
  - `external_standards_report` synthesis paragraph is intact and unchanged.
  - WebFetch instruction is present and clearly marked as sequential.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-audit.md tests/unit/test_audit_parallel_research.py && git commit -m "feat: audit-parallel-research"`*
