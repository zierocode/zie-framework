---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-knowledge-hash-in-implement.md
---

# Remove knowledge-hash Bang Injection from /implement Banner — Implementation Plan

**Goal:** Remove the `knowledge-hash.py --now` bang line from `implement.md` so `/implement` no longer runs a costly rglob+hash subprocess on every invocation.
**Architecture:** Pure line removal from `commands/implement.md`; structural test added to `tests/unit/test_implement_md.py` to lock the absence. Drift detection is already handled by `session-resume.py` fire-and-forget background subprocess at session start — no replacement needed.
**Tech Stack:** Python 3 (test only), Markdown (command file)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/implement.md` | Remove line 15 — `!python3 ... knowledge-hash.py --now` bang injection |
| Create | `tests/unit/test_implement_md.py` | Structural assertion: `knowledge-hash` invocation absent from `implement.md` |

---

## Task 1: Add structural test asserting knowledge-hash absent from implement.md

**Acceptance Criteria:**
- `tests/unit/test_implement_md.py` exists
- Test `test_implement_no_knowledge_hash_bang` asserts `knowledge-hash.py` is not invoked in `implement.md`
- Test FAILS against current `implement.md` (RED — line 15 still present)

**Files:**
- Create: `tests/unit/test_implement_md.py`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  """Structural tests for commands/implement.md."""
  from pathlib import Path

  IMPLEMENT_MD = Path(__file__).parents[2] / "commands" / "implement.md"


  def test_implement_no_knowledge_hash_bang():
      """implement.md must not invoke knowledge-hash.py --now in banner.

      Drift detection is handled by session-resume.py fire-and-forget at session
      start. The bang injection adds subprocess overhead and ~50-100 tokens of
      fingerprint output on every /implement run without actionable value.
      """
      text = IMPLEMENT_MD.read_text()
      assert "knowledge-hash.py" not in text, (
          "implement.md must not contain a knowledge-hash.py bang injection. "
          "Drift detection is covered by session-resume.py at session start."
      )
  ```

  Run: `make test-unit` — must FAIL (line 15 of implement.md contains `knowledge-hash.py`)

- [ ] **Step 2: Implement (GREEN)**

  Remove line 15 from `commands/implement.md`:

  ```
  !`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now 2>/dev/null || echo "knowledge-hash: unavailable"`
  ```

  The banner block (lines 11-16) becomes:

  ```markdown
  **Live context:**
  !`git log -5 --oneline`
  !`git status --short`
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `implement.md` reads naturally without the removed line — no blank lines left, no broken formatting.

  Run: `make test-unit` — still PASS

---
