---
approved: true
approved_at: 2026-03-24
backlog: backlog/reviewer-fail-fast.md
---

# Reviewer Fail-Fast — All Issues in One Pass — Design Spec

**Problem:** Reviewers currently surface issues one at a time, forcing up to 3 round-trips per issue. A plan with 3 issues can require 9 model calls before the reviewer is satisfied.

**Approach:** Update all three reviewer prompts to explicitly return ALL issues found in a single response. Change the iteration pattern in `/zie-plan` and `/zie-implement` from "fix → re-review → fix → re-review" to "initial scan → fix everything → one final confirm pass". Maximum iterations drops from 3-per-issue to 2 total per review cycle.

**Components:**
- Modify: `skills/spec-reviewer/SKILL.md` — update Phase 3 output instructions to surface all issues at once
- Modify: `skills/plan-reviewer/SKILL.md` — same
- Modify: `skills/impl-reviewer/SKILL.md` — same
- Modify: `commands/zie-plan.md` — change reviewer loop to initial pass + single confirm; max 2 iterations total
- Modify: `commands/zie-implement.md` — same iteration change

**Acceptance Criteria:**
- [ ] Each reviewer returns all issues in a single response (not incrementally)
- [ ] Reviewer loop in `/zie-plan` and `/zie-implement` allows max 2 total iterations
- [ ] Second iteration is a "confirm fixed" pass, not a new full review
- [ ] Reviewer checklist content unchanged — only output behavior changes
- [ ] Edge case: 0 issues → APPROVED immediately, no second pass needed

**Out of Scope:**
- Changing what reviewers check
- Model selection (see model-haiku-fast-skills)
- Persistent reviewer memory (see reviewer-agents-memory)
