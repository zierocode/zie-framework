# Skill Content Pruning

## Problem

Several skills contain explanatory prose, inline code examples, and
illustrative comments that consume tokens every time the skill is loaded.
`tdd-loop` has a full quality checklist and cycle time targets. `test-pyramid`
has Playwright config examples and test code snippets. `write-plan` has an
annotated template with explanatory comments. A developer who has used
zie-framework for more than a week already knows this material.

## Motivation

Skill files are loaded into context on every invocation. Trimming examples
and explanatory prose that experienced users don't need reduces the per-skill
token cost by 30–40% without changing any behavior. The core instructions
remain — only the teaching scaffolding is removed.

## Rough Scope

- Audit all 10 skills for: inline code examples, illustrative comments,
  tutorial-style prose, repeated reminders of things stated in the command
- Remove or condense anything that does not change behavior
- Keep: checklists, required steps, format specifications, rules
- Remove: "for example", "note that", worked examples, explanatory analogies
- Out of scope: changing what skills do; removing required output formats
