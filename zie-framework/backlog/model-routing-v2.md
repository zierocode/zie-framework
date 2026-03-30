# Model Routing v2

## Problem

/zie-release uses sonnet for the entire command but 80% of its steps are mechanical file I/O, git commands, and make invocations that require no reasoning — haiku is sufficient and 5–8x cheaper. Similarly, impl-reviewer uses sonnet for all reviews but 90% of routine reviews (AC coverage check, test existence, no secrets scan) are checklist-based tasks haiku handles well. The current model routing doesn't match task complexity to model capability.

## Motivation

Model cost directly affects how freely users run these commands. A /zie-release that costs 5x more than necessary discourages frequent use. Sonnet should be reserved for the 2 steps in release that genuinely require reasoning (version bump rationale, CHANGELOG narrative). For everything else — pre-flight checks, gate result collection, file writes, commit steps — haiku is appropriate and fast. This change reduces release cost by an estimated 30–40% with no quality loss.

## Rough Scope

**In Scope:**
- /zie-release: add `model: haiku` to frontmatter; identify the 2 steps that need sonnet reasoning (version suggestion, CHANGELOG draft) and inline model override for those steps only
- impl-reviewer SKILL.md: change default to haiku; add `<!-- model: sonnet -->` override annotation for complex review tasks (new patterns, security analysis, architectural changes)
- Document the model routing decision in the skill/command frontmatter comments

**Out of Scope:**
- Changing model for spec-design, write-plan, zie-retro, zie-audit (these genuinely need sonnet)
- Adding dynamic model selection at runtime
