---
name: spec-design
description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
argument-hint: "<slug> [full|quick]"
metadata:
  zie_memory_enabled: true
model: sonnet
effort: high
---

# spec-design — Brainstorm → Spec

Turn an idea into a written spec through collaborative dialogue. Output lives in
`zie-framework/specs/`.

## Arguments

| Position | Variable | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Backlog slug (e.g. `my-feature`) | absent → prompt user for slug |
| 1 | `$ARGUMENTS[1]` | Mode: `full` (full dialogue), `quick` (skip clarification, draft directly), or `autonomous` (sprint mode — skip all interactive steps, auto-approve) | absent/empty → `full` |
| 2 | `$ARGUMENTS[2]` | Pass-through flags (e.g. `--draft-plan`); handled by `/spec` control plane, not evaluated by skill | absent/empty → no flags |

**Flag Handling:** `--draft-plan` is parsed and handled by `/spec` command (control plane, per ADR-003).
The skill receives the flag string but does not act on it. Spec-design always writes the spec and runs
the spec-reviewer loop; `/spec` decides whether to auto-proceed to planning.

When `$ARGUMENTS[0]` is absent, fall back to listing the backlog menu and
prompting the user to choose — matching the behaviour of `/spec` with no
argument.

When `$ARGUMENTS[1]` is absent or empty, default to `full` mode. Never raise
an error for a missing second argument.

## เตรียม context

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<feature-area> tags=[spec, design] limit=10`
- Use recalled context to inform design decisions and avoid repeating past
  mistakes.

## Completeness Check (fast path)

When `$ARGUMENTS[0]` is a backlog slug, read the backlog item at
`zie-framework/backlog/<slug>.md` before starting the question flow.
Evaluate the three sections:

- **Problem** — is there substantive content? (≥2 sentences, not just "TBD"
  or a single word)
- **Motivation** — is there substantive content? (≥2 sentences, not just
  "TBD" or a single word)
- **Rough Scope** — is there substantive content? (≥2 sentences, not just
  "TBD" or a single word)

**Fast path:** If all three sections are substantive → skip Step 1
(clarifying questions) entirely and go directly to Step 2 (propose 2-3
approaches), using the backlog content to inform the proposals.

**Normal path:** If any section is thin, missing, or absent → fall through
to Step 1 (clarifying questions) as normal.

This fast-path applies only when a backlog item is provided. When no backlog
slug is given (inline idea path), always start at Step 1.

**`$ARGUMENTS[1]` mode precedence:** When `$ARGUMENTS[1]` is `quick`, that
mode takes effect and this check is skipped. When `full`, clarifying questions
are always asked regardless of completeness.

## Autonomous Mode

When `$ARGUMENTS[1]` is `autonomous`:

- Skip Steps 1, 2, 3 (clarifying questions, approaches proposal, user review loop)
- Write spec directly from backlog content (Step 4) — treat all sections as accepted
- Run spec-reviewer inline (Skill call in same context — no Agent spawn)
- ✅ APPROVED → write `approved: true` frontmatter automatically (Step 6). No user gate.
- ❌ Issues Found → fix inline (1 pass) → re-check once → auto-approve on pass
- On second failure → surface to user (Interruption Protocol case 2)

**Used by:** `/sprint` autonomous execution.
**Not for:** standalone `/spec` — that always uses `full` or `quick`.

## Steps

1. **Understand the idea** — ask clarifying questions one at a time:
   - What problem does this solve?
   - Who uses it and when?
   - What are the success criteria?
   - What is explicitly out of scope?

2. **Propose 2-3 approaches** with trade-offs and a recommendation.

3. **Draft all design sections** in one pass — no approval prompts between sections:
   - Problem & Motivation
   - Architecture & Components
   - Data Flow
   - Edge Cases
   - Out of Scope

   Once all sections are written, present the complete draft to the user.

   **Review the complete draft** — ask the user:
   > "Here is the full spec draft. Does this look right, or would you like
   > any changes?"

   If the user requests changes: apply all requested changes to the draft
   in one batch, re-present the updated draft once, then continue.
   If the user accepts: proceed to Step 4.

   Max one re-draft cycle. If further issues remain after one round of
   edits, surface to the user for section-level guidance before continuing.

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

5. **Spec reviewer loop** — <!-- BLOCKING: do not write frontmatter (Step 6) until reviewer returns ✅ APPROVED -->
   invoke `Skill(zie-framework:spec-reviewer)` with:
   - Path to spec file
   - Backlog item context
   - `context_bundle=<context_bundle>` (pass through for inline fast-path)
   - If ❌ Issues Found → fix issues → re-invoke reviewer → repeat until ✅ APPROVED
   - Max 3 iterations → surface to human

6. **Record approval** — once spec-reviewer returns ✅ APPROVED:

   a. Prepend frontmatter with `approved: false` (gate requires this before approve.py):

   ```yaml
   ---
   approved: false
   approved_at:
   backlog: backlog/<slug>.md
   ---
   ```

   b. Run Bash to flip to approved (the only path the reviewer-gate allows):

   ```bash
   python3 hooks/approve.py zie-framework/specs/YYYY-MM-DD-<slug>-design.md
   ```

7. **Store spec approval in brain** — if `zie_memory_enabled=true`:

   - Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Spec approved: <feature>. Key decisions: [<d1>]." tags=[spec, <project>, <feature-area>]`

8. Print handoff — do NOT auto-invoke write-plan:

   ```text
   Spec approved ✓ (reviewed by spec-reviewer) → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: Run /plan <slug> to draft the implementation plan.
   ```

