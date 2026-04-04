# zie-sprint Phase 1: Invoke Skills Directly Instead of Commands

## Problem

Each Phase 1 parallel agent in `commands/zie-sprint.md:123-132` is prompted to "Invoke `/zie-spec <slug> --draft-plan`" — which internally triggers `spec-design` → `spec-reviewer` → `write-plan` → `plan-reviewer`. This creates 3 levels of nesting (sprint agent → spec command → skill chain). Each nesting level re-serializes context. For a 4-item sprint, this means up to 16 nested skill invocations with repeated context serialization.

## Motivation

The `--draft-plan` shortcut compresses the spec+plan pipeline for single-item flows. Inside a batch sprint, it compounds overhead. Invoking the skills directly (Skill(spec-design) → Skill(spec-reviewer) → Skill(write-plan) → Skill(plan-reviewer)) eliminates one nesting layer per item and avoids the command-level overhead of `/zie-spec`.

## Rough Scope

- Rewrite Phase 1 sprint agent prompts to call skills directly instead of commands
- Remove the `/zie-spec --draft-plan` invocation pattern from sprint agents
- Verify the skill chain produces equivalent output to the command pipeline
- Update sprint integration tests
