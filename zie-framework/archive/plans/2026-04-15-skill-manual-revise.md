---
date: 2026-04-15
status: approved
slug: skill-manual-revise
backlog: backlog/skill-manual-revise.md
---

# skill-manual-revise — Implementation Plan

**Goal:** Compress all 14 SKILL.md files by ~20% total lines while preserving full functionality.
**Architecture:** Manual file-by-file revision using consistent compression tactics.
**Tech Stack:** Markdown, existing skill format.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/*/SKILL.md` (all 14 files) | Compress verbose content |

## Task 1: Establish compression template

<!-- depends_on: none -->

**Acceptance Criteria:**
- A reference pattern exists showing before/after for each compression tactic
- Template covers: argument tables, memory call shorthand, step tightening, prose reduction

**Files:**
- Modify: `skills/debug/SKILL.md` (pilot file — smallest with all pattern types)

- [ ] **Step 1: Write baseline measurement (RED)**
  Create test that counts total SKILL.md lines and asserts baseline = 1492.
  Run: `make test-unit` — must PASS (baseline test exists).

- [ ] **Step 2: Compress pilot file (GREEN)**
  Revise `skills/debug/SKILL.md` using all compression tactics:
  - Collapse `zie_memory_enabled` call blocks to `→ zie-memory: recall(…)` / `→ zie-memory: remember(…)` one-liners
  - Tighten step instructions to short imperatives
  - Remove redundant re-explanations
  Run: `make test-unit` — must PASS.

- [ ] **Step 3: Refactor**
  Extract the compression pattern as a checklist for remaining files.
  Run: `make test-unit` — still PASS.

## Task 2: Compress large files (spec-design, write-plan, brainstorm)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Each file reduced by ~20% lines from original
- All arguments, steps, and behavioural rules preserved
- Frontmatter unchanged

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`
- Modify: `skills/brainstorm/SKILL.md`

- [ ] **Step 1: Write target assertions (RED)**
  Add test assertions for each file: `spec-design ≤ 140`, `write-plan ≤ 115`, `brainstorm ≤ 115`.
  Run: `make test-unit` — must FAIL (files not yet compressed).

- [ ] **Step 2: Compress files (GREEN)**
  Apply compression tactics to all three files. Focus on:
  - Converting prose argument sections to compact tables
  - Collapsing multi-line memory blocks to shorthand
  - Tightening step descriptions
  Run: `make test-unit` — must PASS.

- [ ] **Step 3: Refactor**
  Review compressed files for consistency across the three.
  Run: `make test-unit` — still PASS.

## Task 3: Compress medium files (reviewers, verify, audit, docs-sync-check)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Each file reduced by ~20% lines
- Reviewer loop logic and checklists fully preserved

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `skills/verify/SKILL.md`
- Modify: `skills/zie-audit/SKILL.md`
- Modify: `skills/docs-sync-check/SKILL.md`

- [ ] **Step 1: Compress all six files (GREEN)**
  Apply compression tactics to all six files in one batch.
  Run: `make test-unit` — must PASS.

## Task 4: Compress small files (test-pyramid, tdd-loop, load-context, using-zie-framework)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Each file reduced by ~15-20% lines
- All tables, command maps, and step lists preserved

**Files:**
- Modify: `skills/test-pyramid/SKILL.md`
- Modify: `skills/tdd-loop/SKILL.md`
- Modify: `skills/load-context/SKILL.md`
- Modify: `skills/using-zie-framework/SKILL.md`

- [ ] **Step 1: Compress all four files (GREEN)**
  Apply compression tactics. These are already compact — focus on removing redundancy.
  Run: `make test-unit` — must PASS.

## Task 5: Final verification

<!-- depends_on: Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- Total line count across all SKILL.md files ≤ 1190 (≥20% reduction)
- Every skill still produces correct output when invoked
- No essential instructions lost

**Files:**
- Modify: test file (update line count assertions)

- [ ] **Step 1: Run full verification**
  - `wc -l skills/*/SKILL.md` — total ≤ 1190
  - `make test-unit` — all pass
  - Manual spot-check: invoke 2-3 skills and verify correct behaviour

## Tests

- Unit test: assert total SKILL.md line count after compression
- Unit test: assert each file's line count within target range
- Manual: invoke `spec-design`, `debug`, `tdd-loop` skills and verify output

## Acceptance Criteria

- Total SKILL.md lines ≤ 1190 (≥20% reduction from 1492)
- All 14 files still contain their original arguments, steps, and rules (no functionality lost)
- No frontmatter fields removed or changed (except description tightening)
- `make test-unit` passes