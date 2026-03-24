---
approved: true
approved_at: 2026-03-24
backlog: backlog/spec-design-fast-path.md
---

# spec-design Fast Path for Complete Backlog Items — Design Spec

**Problem:** `spec-design` always asks 4 clarifying questions one at a time before proposing any approach, even when the backlog item already has a complete Problem, Motivation, and Rough Scope. For well-defined items this adds 4 unnecessary round-trips before real design work begins.

**Approach:** At the start of `spec-design`, read the backlog item's three sections. If all three are substantive (each has ≥2 sentences of non-trivial content), skip the clarifying question phase and go directly to proposing 2–3 approaches. If any section is absent, one-line, or vague, fall through to the normal question flow.

**Components:**
- Modify: `skills/spec-design/SKILL.md` — add completeness check at Phase 1: read Problem, Motivation, Rough Scope; evaluate substantiveness; branch to fast-path (approach proposal) or normal path (clarifying questions)

**Acceptance Criteria:**
- [ ] Backlog items with substantive Problem + Motivation + Rough Scope skip clarifying questions
- [ ] Incomplete backlog items (missing or thin sections) still go through question flow
- [ ] "Substantive" = each section has ≥2 sentences with non-trivial content (not just "TBD" or one word)
- [ ] Fast path lands directly at approach proposal step
- [ ] Approach proposal step and all subsequent steps unchanged
- [ ] Fast path does not apply when backlog item is not provided (inline idea path)

**Out of Scope:**
- Changing the approach proposal, design sections, or spec-reviewer steps
