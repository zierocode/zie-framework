---
approved: true
approved_at: 2026-03-23
backlog:
spec: specs/2026-03-23-reviewer-depth-design.md
---

# Reviewer Depth — Implementation Plan

**Goal:** Add a context bundle step to all three reviewer skills so reviews
are cross-referenced against the actual codebase, ADRs, and ROADMAP.

**Architecture:** Three parallel skill file changes — each reviewer gains a
Phase 1 (load context bundle) and three new checklist items. The bundle reads
only files explicitly named in the document under review, plus the ADR
directory, project/context.md, and ROADMAP lanes.

**Tech Stack:** Markdown (skill files), Python/pytest (content validation)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `tests/unit/test_reviewer_depth.py` | Validate all 3 skills contain context bundle |
| Modify | `skills/spec-reviewer/SKILL.md` | Add context bundle + 3 new checks |
| Modify | `skills/plan-reviewer/SKILL.md` | Add context bundle + 3 new checks |
| Modify | `skills/impl-reviewer/SKILL.md` | Add context bundle + 3 new checks |

---

## Task 1: Add context bundle to spec-reviewer

**Acceptance Criteria:**

- `skills/spec-reviewer/SKILL.md` contains a Phase 1 context bundle step
- Phase 1 reads: named component files, `decisions/*.md`, `project/context.md`,
  `ROADMAP.md` (Now + Ready + Next only)
- Three new checks added: file existence, ADR conflict, ROADMAP conflict
- Edge cases covered: missing decisions/ → skip, missing context.md → skip,
  ROADMAP missing → skip
- Bundle read failure never blocks review
- Phase 2 (existing checklist) and Phase 3 (new checks) are distinct

**Files:**

- Create: `tests/unit/test_reviewer_depth.py`
- Modify: `skills/spec-reviewer/SKILL.md`

- [x] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_depth.py
  from pathlib import Path

  ROOT = Path(__file__).parent.parent.parent
  SKILLS = ROOT / "skills"


  def read_skill(name):
      return (SKILLS / name / "SKILL.md").read_text()


  def test_spec_reviewer_has_context_bundle():
      content = read_skill("spec-reviewer")
      assert "context bundle" in content.lower() or "Context Bundle" in content


  def test_spec_reviewer_reads_decisions():
      content = read_skill("spec-reviewer")
      assert "decisions/" in content or "decisions/*.md" in content


  def test_spec_reviewer_reads_roadmap():
      content = read_skill("spec-reviewer")
      assert "ROADMAP" in content


  def test_spec_reviewer_checks_file_existence():
      content = read_skill("spec-reviewer")
      assert "FILE NOT FOUND" in content or "file exist" in content.lower()


  def test_spec_reviewer_checks_adr_conflict():
      content = read_skill("spec-reviewer")
      assert "ADR" in content or "conflict" in content.lower()


  def test_spec_reviewer_checks_roadmap_conflict():
      content = read_skill("spec-reviewer")
      assert "ROADMAP conflict" in content or "duplicate" in content.lower()
  ```

  Run: `make test-unit` — must FAIL (no context bundle in skill yet)

- [x] **Step 2: Implement (GREEN)**

  In `skills/spec-reviewer/SKILL.md`, add before "## Review Checklist":

  ````markdown
  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **Named component files** — parse the spec's **Components** section →
     read each listed file if it exists; note "FILE NOT FOUND" if missing.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.
  4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
     only. If missing → skip ROADMAP conflict check.
  ````

  Then rename existing section to "## Phase 2 — Review Checklist" and add
  after it:

  ````markdown
  ## Phase 3 — Context Checks

  Cross-reference the spec against the loaded bundle:

  10. **File existence** — list any named component files that don't exist.
      Exception: if the spec marks a file as "Create" (new file to be made),
      this is not a failure — note it as expected.
  11. **ADR conflict** — flag any design decision in the spec that contradicts
      a loaded ADR. If no ADRs loaded → skip.
  12. **ROADMAP conflict** — flag if this spec overlaps a Ready or Now item
      (same feature or duplicate scope). If ROADMAP missing → skip.
  ````

  Also update Output Format to show Phase 3 issues under the same `❌ Issues
  Found` block (no separate format).

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Read updated spec-reviewer end-to-end. Verify phase numbering is consistent
  (1 → 2 → 3). Run: `make test-unit` — still PASS

---

## Task 2: Add context bundle to plan-reviewer

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `skills/plan-reviewer/SKILL.md` contains Phase 1 context bundle step
- Three new checks: file map file existence, ADR conflict, codebase pattern
  match (flags divergence, does not decide)
- Edge cases handled same as spec-reviewer
- Existing 9-item checklist renumbered to Phase 2, new checks are Phase 3

**Files:**

- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_depth.py`

- [x] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_reviewer_depth.py`:

  ```python
  def test_plan_reviewer_has_context_bundle():
      content = read_skill("plan-reviewer")
      assert "context bundle" in content.lower() or "Context Bundle" in content


  def test_plan_reviewer_reads_decisions():
      content = read_skill("plan-reviewer")
      assert "decisions/" in content or "decisions/*.md" in content


  def test_plan_reviewer_checks_file_existence():
      content = read_skill("plan-reviewer")
      assert "FILE NOT FOUND" in content or "file exist" in content.lower()


  def test_plan_reviewer_checks_adr_conflict():
      content = read_skill("plan-reviewer")
      assert "ADR" in content or "conflict" in content.lower()


  def test_plan_reviewer_checks_pattern_match():
      content = read_skill("plan-reviewer")
      assert "pattern" in content.lower()


  def test_plan_reviewer_checks_roadmap_conflict():
      content = read_skill("plan-reviewer")
      assert "ROADMAP conflict" in content or "duplicate" in content.lower()
  ```

  Run: `make test-unit` — must FAIL

- [x] **Step 2: Implement (GREEN)**

  Apply the same Phase 1 block as spec-reviewer. For the file map step, use
  "File Map" section instead of Components:

  ````markdown
  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **File map files** — parse the plan's **แผนที่ไฟล์** (file map) section
     → read each listed file if it exists; note "FILE NOT FOUND" if missing.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.
  4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
     only. If missing → skip ROADMAP conflict check.
  ````

  Rename existing checklist to "## Phase 2 — Review Checklist". Add:

  ````markdown
  ## Phase 3 — Context Checks

  10. **File existence** — list any file-map files that don't exist and are
      not marked Create.
  11. **ADR conflict** — flag any planned approach that contradicts a loaded
      ADR. If no ADRs → skip.
  12. **ROADMAP conflict** — flag if this plan overlaps a Ready or Now item
      (same feature or duplicate scope). If ROADMAP missing → skip.
  13. **Pattern match** — flag if the planned approach diverges from patterns
      observed in the read files. Surface the divergence for Zie to accept or
      reject — reviewer notes, does not decide.
  ````

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Read updated plan-reviewer end-to-end. Run: `make test-unit` — still PASS

---

## Task 3: Add context bundle to impl-reviewer

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `skills/impl-reviewer/SKILL.md` contains Phase 1 context bundle step
- Three new checks: modified files exist, ADR compliance, implementation
  pattern match
- No ROADMAP conflict check for impl-reviewer (per spec — out of scope)
- Existing 8-item checklist renumbered to Phase 2, new checks are Phase 3

**Files:**

- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_depth.py`

- [x] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_reviewer_depth.py`:

  ```python
  def test_impl_reviewer_has_context_bundle():
      content = read_skill("impl-reviewer")
      assert "context bundle" in content.lower() or "Context Bundle" in content


  def test_impl_reviewer_reads_decisions():
      content = read_skill("impl-reviewer")
      assert "decisions/" in content or "decisions/*.md" in content


  def test_impl_reviewer_checks_file_existence():
      content = read_skill("impl-reviewer")
      assert "FILE NOT FOUND" in content or "file exist" in content.lower()


  def test_impl_reviewer_no_roadmap_conflict_check():
      # impl-reviewer spec explicitly says no ROADMAP conflict check
      content = read_skill("impl-reviewer")
      assert "ROADMAP conflict" not in content


  def test_impl_reviewer_checks_pattern_match():
      content = read_skill("impl-reviewer")
      assert "pattern" in content.lower()
  ```

  Run: `make test-unit` — must FAIL

- [x] **Step 2: Implement (GREEN)**

  Apply Phase 1 block to impl-reviewer (files come from caller's "List of
  files changed" input):

  ````markdown
  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **Modified files** — read each file listed in the caller's "files changed"
     input; note "FILE NOT FOUND" if any are missing.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.
  ````

  Rename existing checklist to "## Phase 2 — Review Checklist". Add:

  ````markdown
  ## Phase 3 — Context Checks

  9. **File existence** — flag any file in the changed-files list that is
     missing (may indicate incomplete implementation).
  10. **ADR compliance** — flag any implementation detail that contradicts a
      loaded ADR. If no ADRs → skip.
  11. **Pattern match** — flag if implementation diverges from patterns in
      the read files. Surface for Zie to accept or reject — reviewer notes,
      does not decide.
  ````

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Read updated impl-reviewer end-to-end. Verify phase numbering, no ROADMAP
  conflict check present. Run: `make test-unit` — still PASS

---

## Context from brain

_zie_memory_enabled=false — no brain context available._
