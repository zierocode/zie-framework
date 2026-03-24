# ADR-012: Tiered Model Routing — haiku / sonnet / opus per command and skill

Date: 2026-03-24
Status: Accepted

## Context

Prior to v1.6.0, most commands had no `model` or `effort` frontmatter. Claude Code
used the session default model for all commands and skills, regardless of task
complexity. This meant audit analysis (9-dimension, 15+ web searches, cross-reference
synthesis) ran on the same model as a checklist scan. As the framework grew to 22
commands and skills with very different cognitive demands, the lack of routing created
both quality risk (complex tasks may underperform) and cost risk (simple tasks
unnecessarily expensive).

## Decision

Adopt a three-tier model routing policy, applied consistently across all commands
and skills via frontmatter:

- **`model: opus` + `effort: high`** — reserved exclusively for `zie-audit` (command
  and skill). Rationale: 9-dimension codebase analysis + 15+ WebSearch synthesis +
  parallel agent cross-referencing is the most cognitively demanding task in the
  framework. It runs infrequently (periodic health check), so cost is acceptable.
  Quality of findings directly determines backlog priorities.

- **`model: sonnet` + `effort: high|medium`** — design, planning, implementation,
  debugging, release, retro, init, resync. Tasks that require synthesis, generation
  from scratch, or multi-step reasoning.

- **`model: haiku` + `effort: low`** — status check, backlog capture, all reviewer
  skills, reference/process guides (tdd-loop, test-pyramid, retro-format), verify.
  Tasks that are checklist-driven, mechanical, or primarily lookup/read.

All files in `commands/` and `skills/` must have both `model` and `effort` keys.
Enforced by `TestExpectedValues` in `test_model_effort_frontmatter.py`.

## Consequences

**Positive:** Audit analysis gets maximum available reasoning depth. Fast checklist
tasks (reviewers, verify, status) are cheaper and faster. The policy is explicit and
auditable via tests.

**Negative:** Adding a new command or skill requires a deliberate model/effort
assignment decision — no longer a free default. `opus` runs are slower and more
expensive; if zie-audit is called frequently, cost may be noticeable.

**Neutral:** The test file `EXPECTED` map must be updated when new commands or skills
are added, or when routing decisions change.
