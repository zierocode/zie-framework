---
approved: true
approved_at: 2026-04-04
backlog: backlog/consolidate-reviewer-disk-fallback.md
---

# Consolidate Reviewer Disk Fallback — Implementation Plan

**Goal:** Remove the duplicated inline Phase 1 disk-fallback blocks from `spec-reviewer`, `plan-reviewer`, and `impl-reviewer`, replacing each with a compact delegation stub that points to `reviewer-context` as the single source of truth.

**Architecture:** Each reviewer skill currently contains an ~8-line Phase 1 block that re-describes the disk-fallback ADR read logic already owned by `reviewer-context`. This plan replaces those blocks with a compact stub while preserving all test-required anchor strings as inline comments per ADR-048 pattern.

**Tech Stack:** Markdown skill files only — no Python changes.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Replace Phase 1 inline block with compact stub; retain test-anchor comments |
| Modify | `skills/plan-reviewer/SKILL.md` | Replace Phase 1 inline block with compact stub; retain test-anchor comments |
| Modify | `skills/impl-reviewer/SKILL.md` | Replace Phase 1 inline block with compact stub; retain impl-specific anchors |
| No change | `skills/reviewer-context/SKILL.md` | Already the source of truth — untouched |

---

## Task 1: Update spec-reviewer Phase 1

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` Phase 1 contains only a compact delegation stub (no inline ADR read steps)
- All test-required strings remain present: `context bundle`, `if context_bundle provided`, `read from disk`, `write_adr_cache`, `get_cached_adrs`, `ADR-000-summary.md`, `decisions/`, `decisions/ADR-*.md`, `project/context.md`, `ROADMAP`
- `make test-unit` passes — no regressions in `test_reviewer_skill_adr_cache.py`, `test_reviewer_shared_context.py`, `test_reviewer_depth.py`, `test_reviewer_adr_loading.py`

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Verify that the Phase 1 block in spec-reviewer is shorter than 10 lines (i.e., the inline block has been removed). Add a size-gate test:

  ```python
  # tests/unit/test_consolidate_reviewer_disk_fallback.py
  from pathlib import Path

  SKILLS_DIR = Path(__file__).parents[2] / "skills"


  def _phase1_lines(skill_name: str) -> int:
      """Count lines in Phase 1 section of a reviewer skill."""
      text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
      lines = text.splitlines()
      in_phase1 = False
      count = 0
      for line in lines:
          if "## Phase 1" in line:
              in_phase1 = True
              continue
          if in_phase1 and line.startswith("## "):
              break
          if in_phase1:
              count += 1
      return count


  def test_spec_reviewer_phase1_is_compact():
      """Phase 1 must be a stub — no inline ADR read steps."""
      assert _phase1_lines("spec-reviewer") <= 10, (
          "spec-reviewer Phase 1 is too long — inline disk-fallback block not removed"
      )
  ```

  Run: `make test-unit` — must FAIL (current Phase 1 is ~14 lines)

- [ ] **Step 2: Implement (GREEN)**

  Replace the Phase 1 block in `skills/spec-reviewer/SKILL.md`:

  **Remove** this block (lines 26–34):
  ```markdown
  - **if context_bundle provided by caller** — uses `context_bundle.adrs` and
    `context_bundle.context` directly (fast path, skips disk reads)
  - **If `context_bundle` absent** — read from disk: `decisions/*.md` (via
    `get_cached_adrs` cache; summary-aware: reads `ADR-000-summary.md` first,
    then calls `write_adr_cache`), `project/context.md`, `ROADMAP` lanes

  Returns: `adrs_content`, `context_content`.
  ```

  **Replace with** this compact stub:
  ```markdown
  Invoke the `reviewer-context` skill to load shared context.
  <!-- context-load: if context_bundle provided → fast path; absent → read from disk:
       get_cached_adrs → ADR-000-summary.md → decisions/ADR-*.md → write_adr_cache,
       project/context.md, ROADMAP lanes -->

  Returns: `adrs_content`, `context_content`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the Phase 1 heading still reads `## Phase 1 — Load Context Bundle` (no heading change). Confirm no prose duplication between the stub and `reviewer-context/SKILL.md`.

  Run: `make test-unit` — still PASS

---

## Task 2: Update plan-reviewer Phase 1

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/plan-reviewer/SKILL.md` Phase 1 contains only the compact delegation stub
- All test-required strings remain: `context bundle`, `if context_bundle provided`, `read from disk`, `write_adr_cache`, `get_cached_adrs`, `ADR-000-summary.md`, `decisions/`, `decisions/ADR-*.md`, `project/context.md`, `ROADMAP`
- `make test-unit` passes

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_consolidate_reviewer_disk_fallback.py`:

  ```python
  def test_plan_reviewer_phase1_is_compact():
      """Phase 1 must be a stub — no inline ADR read steps."""
      assert _phase1_lines("plan-reviewer") <= 10, (
          "plan-reviewer Phase 1 is too long — inline disk-fallback block not removed"
      )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  Replace the Phase 1 block in `skills/plan-reviewer/SKILL.md` using the same compact stub pattern as Task 1:

  ```markdown
  Invoke the `reviewer-context` skill to load shared context.
  <!-- context-load: if context_bundle provided → fast path; absent → read from disk:
       get_cached_adrs → ADR-000-summary.md → decisions/ADR-*.md → write_adr_cache,
       project/context.md, ROADMAP lanes -->

  Returns: `adrs_content`, `context_content`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm Phase 1 heading unchanged. No prose duplication with `reviewer-context`.

  Run: `make test-unit` — still PASS

---

## Task 3: Update impl-reviewer Phase 1

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` Phase 1 contains only the compact delegation stub
- All test-required strings remain: `context bundle`, `if context_bundle provided`, `read from disk`, `write_adr_cache`, `get_cached_adrs`, `ADR-000-summary.md`, `decisions/`, `adr_cache_path`, `files changed`
- `impl-reviewer` retains its unique note about `adr_cache_path` (JSON cache path variant) as a parenthetical in the stub comment
- `make test-unit` passes

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_consolidate_reviewer_disk_fallback.py`:

  ```python
  def test_impl_reviewer_phase1_is_compact():
      """Phase 1 must be a stub — no inline ADR read steps."""
      assert _phase1_lines("impl-reviewer") <= 12, (
          "impl-reviewer Phase 1 is too long — inline disk-fallback block not removed"
      )
  ```

  (12-line limit allows for the extra `adr_cache_path` note and "read changed files" step.)

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  Replace the Phase 1 block in `skills/impl-reviewer/SKILL.md`. `impl-reviewer` has a slight variant (`adr_cache_path`) — retain it as a parenthetical:

  ```markdown
  Invoke the `reviewer-context` skill to load shared context.
  <!-- context-load: if context_bundle provided → fast path (checks adr_cache_path first,
       then context_bundle.adrs legacy, then disk fallback); absent → read from disk:
       get_cached_adrs → ADR-000-summary.md → decisions/ADR-*.md → write_adr_cache,
       project/context.md -->

  Also read each file listed in the caller's "files changed" input (note "FILE NOT FOUND"
  if any are missing).

  Returns: `adrs_content`, `context_content`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `test_impl_reviewer_no_roadmap_conflict_check` still passes (impl-reviewer must NOT mention `ROADMAP conflict`). Confirm `files changed` and `FILE NOT FOUND` strings still present for test_reviewer_depth.py.

  Run: `make test-unit` — still PASS

---

## Task 4: Verify full suite + lint

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `make test-unit` passes with zero failures
- `make lint` passes with zero violations
- No unintended content removed from any reviewer skill (Phase 2, Phase 3, Output Format, Notes sections unchanged)

**Files:**
- No file changes — verification only

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all tests pass, no regressions.

- [ ] **Step 2: Run lint**

  ```bash
  make lint
  ```

  Expected: zero violations.

- [ ] **Step 3: Spot-check reviewer skills**

  Read `skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`, `skills/impl-reviewer/SKILL.md`.
  Confirm Phase 2, Phase 3, Output Format, Notes sections are identical to pre-change state.
