# ADR-003: Commands Are the Control Plane, Skills Are Execution

Date: 2026-03-23
Status: Accepted

## Context

During the SDLC pipeline redesign, `spec-design/SKILL.md` was written to
auto-invoke `Skill(zie-framework:write-plan)` after the spec reviewer approved
a spec. This caused pipeline divergence: the skill was deciding when to advance
to the next stage, bypassing the user's control plane (/zie-plan command).

The user encountered a situation where running `/zie-spec` would automatically
advance to plan drafting without an explicit `/zie-plan` invocation. This broke
the expected mental model: "I run `/zie-spec`, I get a spec, I run `/zie-plan`
when ready."

## Decision

Commands (`/zie-*`) are the exclusive control plane for pipeline stage
transitions. Skills execute within a single stage but must NOT trigger
advancement to the next stage.

Specifically:

- `spec-design` writes a spec and marks it `approved: true` — then stops.
  It prints "Next: /zie-plan SLUG" but does NOT invoke write-plan.
- `write-plan` drafts a plan and presents it — then stops.
  /zie-plan handles user approval and ROADMAP update.
- No skill may invoke another command-level skill that advances pipeline state.

## Consequences

**Positive:**

- Users have full control over when the pipeline advances.
- Each command can be run independently (idempotent, re-runnable).
- Skills remain composable: /zie-plan can invoke write-plan without coupling.
- Easier to debug: the control flow is visible in the command sequence.

**Negative:**

- Slightly more typing for users (explicit /zie-plan after /zie-spec).
- Skills that previously handed off automatically now require a follow-up
  command.
