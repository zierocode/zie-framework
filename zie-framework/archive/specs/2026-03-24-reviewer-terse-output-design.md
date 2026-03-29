---
approved: true
approved_at: 2026-03-24
backlog: backlog/reviewer-terse-output.md
---

# Reviewer Terse Output — Design Spec

**Problem:** All three reviewers produce verbose output — approvals run 3-5 sentences, issues include prose framing around each bullet. Every invocation adds unnecessary tokens to the context window regardless of outcome.

**Approach:** Constrain the output format for all three reviewers via a strict format spec in each SKILL.md. Approval = exactly `✅ APPROVED` (1 line). Issues = `❌ Issues Found` header + numbered bullet list only — no prose introduction, no closing instructions beyond the fix prompt.

**Components:**
- Modify: `skills/spec-reviewer/SKILL.md` — replace Phase 3 output section with strict format spec (1-line approval OR header + bullets)
- Modify: `skills/plan-reviewer/SKILL.md` — same
- Modify: `skills/impl-reviewer/SKILL.md` — same

**Acceptance Criteria:**
- [ ] Approval output is exactly `✅ APPROVED` — one line, nothing else
- [ ] Issues output starts with `❌ Issues Found` then numbered bullets only
- [ ] No prose introduction before the bullets
- [ ] No multi-sentence closing instructions (one-line fix prompt only, if any)
- [ ] Format is uniform across all three reviewers
- [ ] What is checked (checklists, criteria) is unchanged

**Out of Scope:**
- Changing what is checked by any reviewer
- Changing reviewer iteration logic (see reviewer-fail-fast)
