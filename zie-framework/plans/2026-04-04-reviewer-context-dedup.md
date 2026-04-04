---
approved: true
approved_at: 2026-04-04
backlog: backlog/reviewer-context-dedup.md
---

# Reviewer Context Dedup — Implementation Plan

**Goal:** Remove ~600 words of duplicated Phase 1 prose from three reviewer skills and delete the dead `reviewer-context` skill.
**Architecture:** The three reviewer skills (`spec-reviewer`, `plan-reviewer`, `impl-reviewer`) each inline an identical Phase 1 context-loading block that is already compressed to a 2-line fast-path + disk-fallback summary. The `reviewer-context` standalone skill exists but is never invoked. This plan verifies the Phase 1 blocks are already compressed, deletes the dead skill, and cleans up all references so tests pass.
**Tech Stack:** Markdown (SKILL.md files), Python (unit tests), `make test-unit`

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Delete | `skills/reviewer-context/SKILL.md` | Remove dead skill; leave tombstone note |
| Modify | `zie-framework/PROJECT.md` | Remove `reviewer-context` row from Skills table |
| Modify | `zie-framework/project/components.md` | Remove or tombstone `reviewer-context` row |
| Modify | `tests/unit/test_docs_sync.py` | Remove assertion that `reviewer-context` exists in PROJECT.md |
| Verify (no change) | `skills/spec-reviewer/SKILL.md` | Phase 1 already compressed — confirm, no edit |
| Verify (no change) | `skills/plan-reviewer/SKILL.md` | Phase 1 already compressed — confirm, no edit |
| Verify (no change) | `skills/impl-reviewer/SKILL.md` | Phase 1 already compressed — confirm, no edit |

---

## Task 1: Verify reviewer Phase 1 blocks are already compressed

<!-- depends_on: none -->

**Acceptance Criteria:**
- Each of the three reviewer skills has a Phase 1 section of ≤3 lines (fast-path bullet + disk-fallback bullet + Returns line)
- No reviewer skill calls `Skill(reviewer-context)`

**Files:**
- Read: `skills/spec-reviewer/SKILL.md`
- Read: `skills/plan-reviewer/SKILL.md`
- Read: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  The existing test suite already covers the no-`Skill(reviewer-context)` invariant. Add keyword-order guards (not line-count — line counts are brittle with blank lines):

  ```python
  # tests/unit/test_reviewer_context_chain.py — append these tests

  def _extract_phase1(skill_path: str) -> str:
      text = Path(skill_path).read_text()
      start = text.find("## Phase 1")
      end = text.find("## Phase 2", start)
      return text[start:end]


  def test_spec_reviewer_phase1_structure():
      """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
      phase1 = _extract_phase1("skills/spec-reviewer/SKILL.md")
      assert "**Fast-path:**" in phase1, "spec-reviewer Phase 1 missing Fast-path bullet"
      assert "**Disk fallback:**" in phase1, "spec-reviewer Phase 1 missing Disk fallback bullet"
      assert "Returns:" in phase1, "spec-reviewer Phase 1 missing Returns line"
      assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
          "spec-reviewer Phase 1 bullets out of order"


  def test_plan_reviewer_phase1_structure():
      """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
      phase1 = _extract_phase1("skills/plan-reviewer/SKILL.md")
      assert "**Fast-path:**" in phase1, "plan-reviewer Phase 1 missing Fast-path bullet"
      assert "**Disk fallback:**" in phase1, "plan-reviewer Phase 1 missing Disk fallback bullet"
      assert "Returns:" in phase1, "plan-reviewer Phase 1 missing Returns line"
      assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
          "plan-reviewer Phase 1 bullets out of order"


  def test_impl_reviewer_phase1_structure():
      """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
      phase1 = _extract_phase1("skills/impl-reviewer/SKILL.md")
      assert "**Fast-path:**" in phase1, "impl-reviewer Phase 1 missing Fast-path bullet"
      assert "**Disk fallback:**" in phase1, "impl-reviewer Phase 1 missing Disk fallback bullet"
      assert "Returns:" in phase1, "impl-reviewer Phase 1 missing Returns line"
      assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
          "impl-reviewer Phase 1 bullets out of order"
  ```

  Run: `make test-unit` — these tests may PASS immediately (Phase 1 is already compressed). If they PASS, Task 1 is done with no implementation needed.

- [ ] **Step 2: Implement (GREEN)**

  **Branch condition:** If ALL tests passed in Step 1 → Phase 1 blocks are already compressed. Skip to Step 3 — no edits needed.

  If any test FAILs, compress the offending Phase 1 block to match this exact form:

  For `spec-reviewer` and `plan-reviewer`:
  ```markdown
  ## Phase 1 — Load Context Bundle (inline)

  - **Fast-path:** if context_bundle provided by caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context` · skip disk reads.
  - **Disk fallback:** read from disk — `get_cached_adrs(session_id, "zie-framework/decisions/")` → `adrs_content`; cache miss → read `decisions/ADR-000-summary.md` → `adrs_content`; if missing → fall back: read all `decisions/*.md`; `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`. Read `project/context.md` → `context_content`.

  Returns: `adrs_content`, `context_content`.
  ```

  For `impl-reviewer` (add files-changed line):
  ```markdown
  ## Phase 1 — Load Context Bundle (inline)

  - **Fast-path:** if context_bundle provided by caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context` · skip disk reads.
  - **Disk fallback:** read from disk — `get_cached_adrs(session_id, "zie-framework/decisions/")` → `adrs_content`; cache miss → read `decisions/ADR-000-summary.md` → `adrs_content`; if missing → fall back: read all `decisions/*.md`; `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")` → `adr_cache_path`. Read `project/context.md` → `context_content`.

  Also read each file listed in the caller's "files changed" input (note "FILE NOT FOUND"
  if any are missing).

  Returns: `adrs_content`, `context_content`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No refactor needed — these are doc files.
  Run: `make test-unit` — still PASS

---

## Task 2: Grep for reviewer-context references and plan tombstones

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- A complete list of all non-archive, non-spec files that reference `reviewer-context` is known
- Any file that must keep a reference (e.g. ROADMAP, CHANGELOG) is identified and handled before deletion

**Files:**
- Read: any files surfaced by grep

- [ ] **Step 1: Write failing tests (RED)**

  No new test needed — this is a pre-deletion audit step. Proceed to Step 2.

- [ ] **Step 2: Implement (GREEN)**

  Run the audit:
  ```bash
  grep -rn "reviewer-context" /Users/zie/Code/zie-framework \
    --include="*.py" --include="*.md" --include="*.json" \
    | grep -v "archive/\|specs/\|plans/\|decisions/\|CHANGELOG" \
    | sort
  ```

  Expected references to resolve before deletion:
  - `zie-framework/PROJECT.md` — Skills table row (will be removed in Task 3)
  - `zie-framework/project/components.md` — skill description row (will be removed in Task 3)
  - `zie-framework/ROADMAP.md` — Next lane item (leave as-is; it tracks this backlog item)
  - `tests/unit/test_docs_sync.py` — assertion that PROJECT.md contains `reviewer-context` (will be removed in Task 3)
  - `tests/unit/test_reviewer_context_chain.py` — structural test file (tests confirm no-invoke; keep file, no edit needed)

  If any **non-test, non-doc reference** to `reviewer-context` is found (e.g. a hook, command, or skill invoking it), add a tombstone comment to that file before deletion:
  ```
  <!-- reviewer-context skill deleted — see ADR-054 for canonical context-loading protocol -->
  ```

  Run: `make test-unit` — must PASS (no changes to skill files yet)

- [ ] **Step 3: Refactor**

  Document findings inline in this task's commit message.
  Run: `make test-unit` — still PASS

---

## Task 3: Remove reviewer-context references from docs and tests

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `zie-framework/PROJECT.md` Skills table no longer has a `reviewer-context` row
- `zie-framework/project/components.md` no longer has a live `reviewer-context` row
- `tests/unit/test_docs_sync.py` no longer asserts `reviewer-context` in PROJECT.md

**Files:**
- Modify: `zie-framework/PROJECT.md`
- Modify: `zie-framework/project/components.md`
- Modify: `tests/unit/test_docs_sync.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a test that asserts `reviewer-context` is NOT in PROJECT.md Skills table (post-deletion):

  ```python
  # tests/unit/test_reviewer_context_chain.py — append

  def test_project_md_no_reviewer_context_row():
      """PROJECT.md Skills table must not list reviewer-context after deletion."""
      text = Path("zie-framework/PROJECT.md").read_text()
      # Check only the Skills section
      start = text.find("## Skills") if "## Skills" in text else 0
      end = text.find("\n## ", start + 1) if "\n## " in text[start+1:] else len(text)
      skills_section = text[start:end]
      assert "reviewer-context" not in skills_section, (
          "PROJECT.md Skills table still lists reviewer-context — should be removed"
      )
  ```

  Run: `make test-unit` — must FAIL (reviewer-context still in PROJECT.md)

- [ ] **Step 2: Implement (GREEN)**

  **Edit `zie-framework/PROJECT.md`** — remove the `reviewer-context` row:
  ```
  Remove: | reviewer-context | Load reviewer context (ADRs + ROADMAP) for spec/plan/impl reviewer skills |
  ```

  **Edit `zie-framework/project/components.md`** — remove the `reviewer-context` row entirely (the row describes it as "no longer auto-invoked"; with the skill deleted, the row is obsolete):
  ```
  Remove: | reviewer-context | Shared context-load protocol; no longer auto-invoked in reviewer chain (ADR-054, v1.19.0) — each reviewer now loads context inline. Available for explicit call if needed. | (optional, caller-explicit) |
  ```

  **Edit `tests/unit/test_docs_sync.py`** — remove the assertion:
  ```python
  # Remove these two lines:
  assert "reviewer-context" in self._content(), (
      "PROJECT.md Skills table missing reviewer-context"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify no stray `reviewer-context` references remain in docs (excluding ROADMAP + CHANGELOG + archive):
  ```bash
  grep -rn "reviewer-context" /Users/zie/Code/zie-framework/zie-framework \
    --include="*.md" \
    | grep -v "ROADMAP\|CHANGELOG\|archive/\|specs/\|plans/\|decisions/"
  ```
  Expected output: empty (or only backlog file which is OK to leave).

  Run: `make test-unit` — still PASS

---

## Task 4: Delete skills/reviewer-context/SKILL.md

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `skills/reviewer-context/SKILL.md` is deleted
- `skills/reviewer-context/` directory is removed
- `make test-unit` passes with no regressions

**Files:**
- Delete: `skills/reviewer-context/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add a test that confirms the file is absent:

  ```python
  # tests/unit/test_reviewer_context_chain.py — append

  def test_reviewer_context_skill_deleted():
      """reviewer-context skill must be deleted — it is dead code (ADR-054)."""
      skill_path = Path("skills/reviewer-context/SKILL.md")
      assert not skill_path.exists(), (
          "skills/reviewer-context/SKILL.md still exists — delete it (ADR-054)"
      )
  ```

  Run: `make test-unit` — must FAIL (file still exists)

- [ ] **Step 2: Implement (GREEN)**

  ```bash
  rm -rf /Users/zie/Code/zie-framework/skills/reviewer-context/
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm full test suite still green:
  ```bash
  make test-unit
  ```
  Expected: all tests pass, no import errors, no file-not-found errors.
  Run: `make test-unit` — still PASS
