---
name: spec-design
description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
metadata:
  zie_memory_enabled: true
---

# spec-design — Brainstorm → Spec

Turn an idea into a written spec through collaborative dialogue. Output lives in `zie-framework/specs/`.

## เตรียม context

If `zie_memory_enabled=true`:

- `recall project=<project> domain=<feature-area> tags=[spec, design] limit=10`
- Use recalled context to inform design decisions and avoid repeating past mistakes.

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

5. **Ask user to review** the written spec before proceeding.

6. If approved → hand off to `Skill(zie-framework:write-plan)`.

## Notes

- One question at a time — don't overwhelm
- YAGNI: remove unnecessary features from all designs
- Never skip to implementation without an approved spec
