---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-impl-reviewer-effort-medium-to-low.md
---

# Drop impl-reviewer Effort medium → low — Implementation Plan

**Goal:** Change `effort: medium` to `effort: low` in `skills/impl-reviewer/SKILL.md` and update the corresponding test assertion.
**Architecture:** Single-file frontmatter change plus test map update. No runtime logic modified — only the YAML key that governs token budget for the haiku subagent.
**Tech Stack:** Markdown (YAML frontmatter), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/impl-reviewer/SKILL.md` | Change `effort: medium` → `effort: low` in frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update `EXPECTED` map: `impl-reviewer` from `"medium"` → `"low"` |

---

## Task 1: Update SKILL.md frontmatter

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` frontmatter contains `effort: low`
- `model: haiku` is unchanged
- All other frontmatter keys are unchanged

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing test (RED)**
  Run `make test-unit` now — `TestExpectedValues::test_correct_effort_values` already passes because the EXPECTED map still says `"medium"`. No code to write; confirm baseline is green before changing anything.
  Run: `make test-unit` — must PASS (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In `skills/impl-reviewer/SKILL.md`, change line:
  ```yaml
  effort: medium
  ```
  to:
  ```yaml
  effort: low
  ```
  Run: `make test-unit` — `test_correct_effort_values` will now FAIL (EXPECTED still says `"medium"`). This is the expected RED state.

- [ ] **Step 3: Refactor**
  No refactor needed. Proceed to Task 2 to update the test.
  Run: `make test-unit` — still FAIL (intentional, fixed in Task 2)

---

## Task 2: Update test assertion

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `EXPECTED["skills/impl-reviewer/SKILL.md"]` is `("haiku", "low")`
- `TestExpectedValues::test_correct_effort_values` passes
- `TestHaikuFiles::test_haiku_files_have_low_effort` does NOT cover impl-reviewer (it is not in `EXPECTED_HAIKU`) — no change needed there
- Full `make test-unit` suite passes

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing test (RED)**
  The test is already failing after Task 1 (impl-reviewer frontmatter says `low`, EXPECTED still says `medium`). Confirm:
  Run: `make test-unit` — `test_correct_effort_values` FAILS

- [ ] **Step 2: Implement (GREEN)**
  In `tests/unit/test_model_effort_frontmatter.py`, change line 35:
  ```python
  "skills/impl-reviewer/SKILL.md": ("haiku", "medium"),
  ```
  to:
  ```python
  "skills/impl-reviewer/SKILL.md": ("haiku", "low"),
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactor needed. Verify full suite passes cleanly.
  Run: `make test-unit` — still PASS
