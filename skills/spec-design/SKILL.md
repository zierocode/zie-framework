---
name: spec-design
description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
argument-hint: "<slug> [full|quick]"
metadata:
  zie_memory_enabled: true
model: sonnet
effort: medium
---

# spec-design — Brainstorm → Spec

Turn an idea into a written spec through collaborative dialogue. Output lives in `zie-framework/specs/`.

## Arguments

| Pos | Var | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Backlog slug (e.g. `my-feature`) | absent → list backlog menu, prompt user |
| 1 | `$ARGUMENTS[1]` | `full` (dialogue), `quick` (skip clarification, draft directly), `autonomous` (sprint mode — skip all interactive steps, auto-approve) | absent/empty → `full` |
| 2 | `$ARGUMENTS[2]` | Pass-through flags (e.g. `--draft-plan`); handled by `/spec` control plane (ADR-003), not evaluated by skill | absent/empty → no flags |

Never raise an error for a missing second argument.

## เตรียม context

- If `context_bundle` provided (from `/spec` or `/sprint`): use it directly — skip redundant reads.
- If absent: invoke `Skill(zie-framework:load-context)` to load ADR summary + project context.
- If `zie_memory_enabled=true`: → zie-memory: recall(project=`<project>`, domain=`<feature-area>`, tags=[spec, design], limit=10). Use recalled context to inform design decisions and avoid past mistakes.

## Completeness Check (fast path)

When `$ARGUMENTS[0]` is a backlog slug, read `zie-framework/backlog/<slug>.md` and evaluate three sections:

| Section | Substantive = |
| --- | --- |
| Problem | ≥2 sentences, not just "TBD" or a single word |
| Motivation | ≥2 sentences, not just "TBD" or a single word |
| Rough Scope | ≥2 sentences, not just "TBD" or a single word |

- **Fast path:** All three substantive → skip Step 1, go directly to Step 2 (propose 2-3 approaches).
- **Normal path:** Any section thin/missing/absent → fall through to Step 1.
- No backlog slug (inline idea) → always start at Step 1.
- **`quick` mode** takes precedence — completeness check is skipped. **`full` mode** always asks clarifying questions.

## Autonomous Mode

When `$ARGUMENTS[1]` is `autonomous`:

- Skip Steps 1–3 (clarifying questions, approaches, user review loop).
- Write spec directly from backlog content (Step 5) — treat all sections as accepted.
- Step 5 (Blind Spots check) runs automatically — add findings to Edge Cases section.
- Run spec-reviewer inline (Skill call in same context — no Agent spawn).
- ✅ APPROVED → follow Step 7 exactly: write frontmatter `approved: false`, then `python3 hooks/approve.py <spec-file>` via Bash. Do NOT use Write/Edit to set `approved: true` — reviewer-gate blocks it.
- ❌ Issues Found → fix all issues inline → verify each fix against issue list → run approve.py. Any issue unfixable → surface to user (Interruption Protocol case 2).

**Used by:** `/sprint` autonomous execution. **Not for:** standalone `/spec` — always uses `full` or `quick`.

## Steps

1. **Understand the idea** — ask clarifying questions one at a time: What problem? Who uses it and when? Success criteria? Explicitly out of scope?

2. **Propose 2-3 approaches** with trade-offs and a recommendation.

3. **Draft all design sections** in one pass — no approval prompts between sections:
   Problem & Motivation · Architecture & Components · Data Flow · Edge Cases · Out of Scope

   Present the complete draft. Ask: > "Here is the full spec draft. Does this look right, or would you like any changes?"

   User requests changes → apply all in one batch, re-present once, then continue. User accepts → proceed to Step 4. Max one re-draft cycle; if further issues remain, surface for section-level guidance.

4. **Blind Spots check** — before reviewer, explicitly consider:
   - What does this spec NOT cover? List gaps in scope.
   - What are the failure modes? What happens when assumptions are wrong?
   - What alternatives were considered but rejected? Why?
   - What downstream impacts might this have on other parts of the system?
   Add findings to the spec's Edge Cases section. If no blind spots found, note "No additional blind spots identified."

5. **Write spec** to `zie-framework/specs/YYYY-MM-DD-<feature-slug>-design.md`

   ```markdown
   # <Feature Name> — Design Spec

   **Problem:** <one sentence>
   **Approach:** <2-3 sentences>
   **Components:** <list of affected files/modules>
   **Data Flow:** <step-by-step>
   **Edge Cases:** <list>
   **Out of Scope:** <list>
   ```

6. **Spec reviewer loop** — <!-- BLOCKING: do not write frontmatter (Step 7) until reviewer returns ✅ APPROVED -->
   invoke `Skill(zie-framework:spec-reviewer)` once with: spec file path, backlog item context, `context_bundle=<context_bundle>` (pass through for inline fast-path).
   - ✅ APPROVED → proceed to Step 7
   - ❌ Issues Found → fix all issues inline → verify each fix against the issue list (no re-invocation — inline verification replaces confirm pass)
   - If any issue cannot be fixed → surface to user

7. **Record approval** — once spec-reviewer returns ✅ APPROVED:

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

8. **Store spec approval in brain** — if `zie_memory_enabled=true`: → zie-memory: remember("Spec approved: <feature>. Key decisions: [<d1>].", tags=[spec, `<project>`, `<feature-area>`])

9. Print handoff — do NOT auto-invoke write-plan:
   ```text
   Spec approved ✓ (reviewed by spec-reviewer) → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: Run /plan <slug> to draft the implementation plan.
   ```

