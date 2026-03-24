---
approved: true
approved_at: 2026-03-24
backlog: backlog/spec-design-batch-approval.md
---

# spec-design Batch Section Approval — Design Spec

**Problem:** `spec-design` presents and seeks approval after each section sequentially — Problem, Architecture, Data Flow, Edge Cases, Out of Scope — resulting in 5 separate approval round-trips to produce one spec document.

**Approach:** Draft all sections in one pass without intermediate approval prompts. Present the complete draft to the user once for review. Apply all requested changes at once and re-present once if needed. Proceed to spec-reviewer only after the user accepts the full draft.

**Components:**
- Modify: `skills/spec-design/SKILL.md` — replace section-by-section approval loop with single full-draft presentation; keep all section content and order; add single-review prompt after full draft; apply all edits in one batch if changes requested

**Acceptance Criteria:**
- [ ] All sections (Problem, Architecture, Data Flow, Edge Cases, Out of Scope) written before any approval prompt
- [ ] Single review prompt presented after complete draft
- [ ] User change requests applied to all sections at once; draft re-presented once
- [ ] spec-reviewer invoked only after user accepts the full draft
- [ ] Section content, order, and structure unchanged
- [ ] Max one re-draft cycle before escalating to user for section-level guidance

**Out of Scope:**
- Changing what sections appear in a spec
- Changing spec-reviewer checklist or behavior
