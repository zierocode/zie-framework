---
approved: true
approved_at: 2026-03-24
backlog: backlog/skill-content-pruning.md
---

# Skill Content Pruning — Design Spec

**Problem:** Several skill files contain tutorial prose, inline code examples, and illustrative comments that load into context on every invocation. `tdd-loop` has full quality checklists and cycle time targets. `test-pyramid` has Playwright config examples. `write-plan` has an annotated template with explanatory comments. Experienced users gain nothing from this scaffolding on every call.

**Approach:** Audit all 10 skills and remove content that does not change behavior: "for example" blocks, worked examples, analogies, repeated reminders of things stated elsewhere, inline code examples used only for illustration. Preserve everything that does change behavior: checklists, required output formats, rules, step sequences.

**Components:**
- Modify: `skills/tdd-loop/SKILL.md` — remove cycle time targets, quality analogies, repeated reminders
- Modify: `skills/test-pyramid/SKILL.md` — remove Playwright config examples and code snippets used only for illustration
- Modify: `skills/write-plan/SKILL.md` — remove annotated template explanatory comments; keep format spec
- Modify: `skills/spec-design/SKILL.md` — remove tutorial-style prose that restates the process
- Modify: `skills/spec-reviewer/SKILL.md` — remove illustrative examples of good/bad specs
- Modify: `skills/plan-reviewer/SKILL.md` — same
- Modify: `skills/impl-reviewer/SKILL.md` — same
- Modify: `skills/debug/SKILL.md` — remove "for example" blocks
- Modify: `skills/verify/SKILL.md` — remove explanatory notes around each check
- Modify: `skills/retro-format/SKILL.md` — remove worked ADR examples

**Acceptance Criteria:**
- [ ] All 10 skills audited for removable content
- [ ] ≥30% token reduction in at least 5 skills (estimated by line count)
- [ ] No behavioral change in any skill's output or steps
- [ ] Checklists, required formats, and decision rules preserved in all skills
- [ ] Each modified skill still produces correct output when invoked

**Out of Scope:**
- Changing what any skill does
- Removing required output format specifications
