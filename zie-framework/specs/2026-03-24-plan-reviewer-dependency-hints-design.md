---
approved: true
approved_at: 2026-03-24
backlog: backlog/plan-reviewer-dependency-hints.md
---

# plan-reviewer Dependency Hints — Design Spec

**Problem:** `plan-reviewer` never evaluates task parallelism. Tasks without `<!-- depends_on: -->` annotations run sequentially in `/zie-implement` even when fully independent, because plan authors rarely think to add them.

**Approach:** Add a dependency scan to plan-reviewer Phase 2 that examines each task pair for shared file modifications and data dependencies. Independent task pairs without `depends_on` annotations are flagged as a **suggestion** (not an error) with specific task IDs. This is advisory — the reviewer does not automatically add annotations or fail the plan.

**Components:**
- Modify: `skills/plan-reviewer/SKILL.md` — add dependency scan to Phase 2 checklist: identify tasks with no shared files and no sequential data dependency; output suggestion format: "Tasks N and M appear independent — consider adding `<!-- depends_on: -->` to enable parallel execution"

**Acceptance Criteria:**
- [ ] Phase 2 scans all task pairs for shared file overlap and data dependencies
- [ ] Independent pairs without `depends_on` generate a suggestion (not a blocking issue)
- [ ] Suggestion output includes specific task IDs (e.g., "Tasks 3 and 5")
- [ ] Tasks with shared files or sequential logic are not flagged
- [ ] Suggestion does not cause plan-reviewer to return `Issues Found` — plan can still be APPROVED with suggestions present
- [ ] Existing Phase 1, 2, 3 checks unchanged

**Out of Scope:**
- Automatically inserting `depends_on` annotations into the plan
- Changing how `depends_on` is processed in `/zie-implement`
