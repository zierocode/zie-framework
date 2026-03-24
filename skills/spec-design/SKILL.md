---
name: spec-design
description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
argument-hint: "<slug> [full|quick]"
metadata:
  zie_memory_enabled: true
effort: high
---

# spec-design — Brainstorm → Spec

Turn an idea into a written spec through collaborative dialogue. Output lives in
`zie-framework/specs/`.

## Arguments

| Position | Variable | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Backlog slug (e.g. `my-feature`) | absent → prompt user for slug |
| 1 | `$ARGUMENTS[1]` | Mode: `full` (full dialogue) or `quick` (skip clarification, draft directly) | absent/empty → `full` |

When `$ARGUMENTS[0]` is absent, fall back to listing the backlog menu and
prompting the user to choose — matching the behaviour of `/zie-spec` with no
argument.

When `$ARGUMENTS[1]` is absent or empty, default to `full` mode. Never raise
an error for a missing second argument.

> **Note for future skill authors:** if this skill bundles helper scripts,
> reference them via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — Claude Code
> resolves this to the skill's own directory regardless of CWD.

## เตรียม context

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<feature-area> tags=[spec, design] limit=10`
- Use recalled context to inform design decisions and avoid repeating past
  mistakes.

## Steps

1. **Understand the idea** — ask clarifying questions one at a time:
   - What problem does this solve?
   - Who uses it and when?
   - What are the success criteria?
   - What is explicitly out of scope?

2. **Propose 2-3 approaches** with trade-offs and a recommendation.

3. **Present design sections** — get approval after each:
   - Problem & Motivation
   - Architecture & Components
   - Data Flow
   - Edge Cases
   - Out of Scope

4. **Write spec** to `zie-framework/specs/YYYY-MM-DD-<feature-slug>-design.md`

   Format:

   ```markdown
   # <Feature Name> — Design Spec

   **Problem:** <one sentence>
   **Approach:** <2-3 sentences>
   **Components:** <list of affected files/modules>
   **Data Flow:** <step-by-step>
   **Edge Cases:** <list>
   **Out of Scope:** <list>
   ```

5. **Spec reviewer loop** — dispatch `@agent-spec-reviewer` with:
   <!-- fallback: Skill(zie-framework:spec-reviewer) -->
   - Path to spec file
   - Backlog item context
   - If ❌ Issues Found → fix issues → re-invoke reviewer → repeat until ✅ APPROVED
   - Max 3 iterations → surface to human

6. **Record approval** — once spec-reviewer returns ✅ APPROVED, prepend
   frontmatter to the spec file:

   ```yaml
   ---
   approved: true
   approved_at: YYYY-MM-DD
   backlog: backlog/<slug>.md
   ---
   ```

7. **Store spec approval in brain** — if `zie_memory_enabled=true`:

   - Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Spec approved: <feature>. Key decisions: [<d1>]." tags=[spec, <project>, <feature-area>]`

8. **Ask user to review** the written spec before proceeding.

9. Print handoff — do NOT auto-invoke write-plan:

   ```text
   Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: Run /zie-plan <slug> to draft the implementation plan.
   ```

## Notes

- One question at a time — don't overwhelm
- YAGNI: remove unnecessary features from all designs
- Never skip to implementation without an approved spec
