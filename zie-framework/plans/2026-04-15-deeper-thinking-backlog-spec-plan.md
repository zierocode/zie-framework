---
approved: true
approved_at: 2026-04-15
backlog: backlog/deeper-thinking-backlog-spec-plan.md
---

# Deeper Thinking in Backlog Spec Plan — Implementation Plan

**Goal:** Add "think deeper" prompts to backlog, spec-design, write-plan, and reviewer phases so the framework proactively surfaces blind spots, edge cases, and risks instead of just transcribing user input.
**Architecture:** Five Markdown-only changes — add a "Considerations" section to backlog output, a "Blind Spots" check to spec-design, a "Risk Review" step to write-plan, and extend both reviewers to flag unquestioned assumptions and missing rollbacks. All additions are inline prompt text in existing skill/command files, no new code.
**Tech Stack:** Markdown (skills/commands), no new Python code

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/backlog.md` | Add "Considerations" section to backlog output template |
| Modify | `skills/spec-design/SKILL.md` | Add "Blind Spots" check between draft and reviewer |
| Modify | `skills/write-plan/SKILL.md` | Add "Risk Review" step before file map |
| Modify | `skills/spec-review/SKILL.md` | Extend YAGNI check to flag unquestioned assumptions |
| Modify | `skills/plan-review/SKILL.md` | Add missing-rollback and hidden-dependency checks |

---

## Task 1: Add Considerations section to backlog

<!-- depends_on: none -->

**Acceptance Criteria:**
- backlog.md Step 4 template includes a `## Considerations` section after `## Rough Scope`
- The section auto-suggests 2-3 edge cases, risks, or dependencies
- If no relevant suggestions, the section can be empty
- Existing backlog items are not affected (no retroactive changes)

**Files:**
- Modify: `commands/backlog.md`

- [ ] **Step 1: Read current backlog.md Step 4 template**
  Read `commands/backlog.md` lines 67-87 to get exact template text.

- [ ] **Step 2: Add Considerations section to template**
  After the `## Rough Scope` section in Step 4, add:
  ```markdown
  ## Considerations

  <!-- Auto-suggested: 2-3 edge cases, risks, or dependencies the user may have missed. Remove if none are relevant. -->
  1. <edge case or risk — e.g., "What happens if X fails?" or "Depends on Y which may not be available">
  2. <alternative approach or non-obvious impact>
  3. <dependency or ordering concern>
  ```
  And in Step 4 instructions, add after the template:
  ```
  Fill in Considerations by thinking about: failure modes, dependencies on other systems, 
  edge cases the user may not have considered, and alternatives that might be simpler. 
  If none are relevant, leave the section empty.
  ```

- [ ] **Step 3: Verify Considerations section was added**
  ```bash
  grep -n "Considerations" commands/backlog.md
  ```
  Expected: at least one match for "## Considerations" or "Considerations" section header

  Run: `make test-unit` — not applicable (Markdown-only change)

## Task 2: Add Blind Spots check to spec-design

<!-- depends_on: none -->

**Acceptance Criteria:**
- spec-design SKILL.md has a new step between Step 3 (draft) and Step 5 (reviewer) called "Blind Spots check"
- The step explicitly lists what the spec doesn't cover, failure modes, and alternatives considered
- Autonomous mode includes the Blind Spots check (runs inline, no user interaction)
- The check produces output that gets included in the spec's Edge Cases section

**Files:**
- Modify: `skills/spec-design/SKILL.md`

- [ ] **Step 1: Read current spec-design SKILL.md Steps section**
  Read `skills/spec-design/SKILL.md` lines ~60-70 to get exact text around Step 3 and Step 5.

- [ ] **Step 2: Add Blind Spots check step**
  Insert a new step between current Step 3 (draft) and current Step 5 (reviewer). Renumber:
  - Step 3 stays (draft all sections)
  - New Step 4: **Blind Spots check** — before sending to reviewer:
    ```
    4. **Blind Spots check** — before reviewer, explicitly consider:
       - What does this spec NOT cover? List gaps in scope.
       - What are the failure modes? What happens when assumptions are wrong?
       - What alternatives were considered but rejected? Why?
       - What downstream impacts might this have on other parts of the system?
       Add findings to the spec's Edge Cases section. If no blind spots found, note "No additional blind spots identified."
    ```
  - Old Step 4 → Step 5 (write spec file — renumber)
  - Old Step 5 → Step 6 (reviewer loop — renumber)
  - Old Step 6 → Step 7 (record approval — renumber)
  - Old Step 7 → Step 8 (store in brain — renumber)
  - Old Step 8 → Step 9 (print handoff — renumber)

  In Autonomous mode section, add:
  ```
  - Step 4 (Blind Spots check) runs automatically — add findings to Edge Cases
  ```

- [ ] **Step 3: Verify Blind Spots check was added**
  ```bash
  grep -n "Blind Spot" skills/spec-design/SKILL.md
  ```
  Expected: at least one match for "Blind Spots check" step

  Run: `make test-unit` — not applicable (Markdown-only change)

## Task 3: Add Risk Review step to write-plan

<!-- depends_on: none -->

**Acceptance Criteria:**
- write-plan SKILL.md has a "Risk Review" step before the File Map section
- Each task gets a one-line rollback/rollback strategy note
- Hidden dependencies and ordering risks are flagged
- Plan document template includes a Risk section

**Files:**
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Read current write-plan SKILL.md**
  Read `skills/write-plan/SKILL.md` lines ~48-66 to get exact text around File Map and Task Sizing.

- [ ] **Step 2: Add Risk Review step**
  Insert a new section between "Task Sizing Guidance" and "Task Structure":
  ```markdown
  ## Risk Review

  Before defining tasks, review the spec for:

  1. **Hidden dependencies** — does any task depend on an external system, tool, or file that isn't listed in Components? Flag it.
  2. **Ordering risks** — could tasks fail if run in the wrong order? Add `depends_on` comments.
  3. **Rollback strategy** — for each task, add a one-line rollback note:
     - Deletion tasks: "Rollback: restore from git"
     - Modification tasks: "Rollback: revert the specific change"
     - Creation tasks: "Rollback: delete the created file"

  Include findings in the plan as:
  - `depends_on` comments on tasks with hidden dependencies
  - A rollback note in each task's acceptance criteria
  ```

  Also update the plan template header to include:
  ```markdown
  **Risk Review:** <1-2 sentences about hidden dependencies or ordering risks>
  ```

- [ ] **Step 3: Verify Risk Review section was added**
  ```bash
  grep -n "Risk Review" skills/write-plan/SKILL.md
  ```
  Expected: at least one match for "## Risk Review" section header

  Run: `make test-unit` — not applicable (Markdown-only change)

## Task 4: Extend spec-review with unquestioned assumptions check

<!-- depends_on: none -->

**Acceptance Criteria:**
- spec-review Phase 2 checklist has a new item: "Unquestioned assumptions — things the spec takes for granted without evidence"
- The check is advisory (non-blocking) — flags items but doesn't block APPROVED
- Output format updated to include assumption flags

**Files:**
- Modify: `skills/spec-review/SKILL.md`

- [ ] **Step 1: Read current spec-review Phase 2 checklist**
  Read `skills/spec-review/SKILL.md` lines ~39-49 to get exact Phase 2 checklist.

- [ ] **Step 2: Add unquestioned assumptions check**
  After item 7 (YAGNI), add:
  ```markdown
  8. **Unquestioned assumptions** — things the spec assumes without evidence (e.g., "users will always have X", "Y is available", "Z won't change"). Flag as advisory (non-blocking) — author decides whether to address.
  ```
  Renumber existing items 8→9, 9→10.

- [ ] **Step 3: Verify unquestioned assumptions check was added**
  ```bash
  grep -n "Unquestioned assumption" skills/spec-review/SKILL.md
  ```
  Expected: at least one match for "Unquestioned assumptions" checklist item

  Run: `make test-unit` — not applicable (Markdown-only change)

## Task 5: Extend plan-review with missing-rollback and hidden-dependency checks

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- plan-review Phase 2 checklist has two new items: "Missing rollback" and "Hidden dependencies"
- Both are advisory (non-blocking) — flags items but doesn't block APPROVED
- The "dependency hints" step (item 10) now cross-references with the new "Hidden dependencies" check

**Files:**
- Modify: `skills/plan-review/SKILL.md`

- [ ] **Step 1: Read current plan-review Phase 2 checklist**
  Read `skills/plan-review/SKILL.md` lines ~39-53 to get exact Phase 2 checklist.

- [ ] **Step 2: Add missing-rollback and hidden-dependency checks**
  After item 9 (YAGNI), add:
  ```markdown
  10. **Missing rollback** — tasks that delete, modify, or restructure files without a rollback strategy. Flag as advisory (non-blocking). Example: "Task 2 deletes .github/ — no rollback note. Consider: 'Rollback: git restore .github/'"
  11. **Hidden dependencies** — tasks that depend on external systems, tools, or files not listed in Components. Flag as advisory. Example: "Task 1 depends on utils_cache.py being importable — not listed in File Map"
  ```
  Renumber existing item 10→12 (dependency hints).

  Run: `make test-unit` — not applicable (Markdown-only change)

- [ ] **Step 3: Verify all 5 files are consistent**
  After Tasks 1-4 are complete, check that the "think deeper" theme is consistent across all modified files:
  ```bash
  grep -n "Considerations\|Blind Spot\|Risk Review\|Unquestioned assumption\|Missing rollback\|Hidden dependenc" commands/backlog.md skills/spec-design/SKILL.md skills/write-plan/SKILL.md skills/spec-review/SKILL.md skills/plan-review/SKILL.md
  ```
  Expected: each file has at least one match for its respective addition

  Run: `make test-unit` — not applicable (Markdown-only changes across all files)