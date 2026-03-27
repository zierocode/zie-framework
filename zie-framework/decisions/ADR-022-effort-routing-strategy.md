# ADR-022: Effort Routing Strategy for Skills and Commands
Date: 2026-03-27
Status: Accepted

## Context
zie-framework routes tasks to different model tiers based on `effort:` frontmatter
in skills and commands. With Sonnet 4.6 as the default medium model, `effort: high`
should be reserved for tasks requiring deep reasoning loops or full dialogue cycles.
Sprint 3 audit found `write-plan` skill incorrectly tagged as `high` — it follows
a deterministic template pattern that fits `medium`.

## Decision
`effort: high` is reserved for skills/commands that require full deliberative
reasoning cycles: `spec-design` (open-ended problem framing, multi-turn dialogue)
only. All other skills and commands use `effort: medium` (Sonnet 4.6) or
`effort: low` (fast reviewer/formatter tasks). `write-plan` changed from `high`
→ `medium`. Commands audit confirmed all commands already at `medium` or `low`.

## Consequences
- Lower cost per `/zie-plan` invocation (write-plan no longer triggers high-effort routing)
- `spec-design` retains `high` for full dialogue quality
- Future skills default to `medium` unless deep reasoning loop explicitly required
- Documented in SKILL.md frontmatter — any regression caught by test_effort_audit.py
