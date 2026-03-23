---
approved: true
approved_at: 2026-03-23
backlog:
reviewed_iterations: 1
---

# Quick Spec — Design Spec

**Problem:** Every idea requires a backlog file before `/zie-spec` can run,
adding friction for small, well-understood tasks where the developer already
knows what they want to build.

**Approach:** Extend `/zie-spec` to accept an inline idea string as an
argument. When an inline idea is given, skip the backlog file requirement and
pass the idea directly to `spec-design`. The existing slug path is unchanged.
No backlog file is created — intentional.

**Components:**

- `commands/zie-spec.md` — detect inline idea vs slug; add quick-spec input
  mode that bypasses backlog file lookup

**Data Flow:**

```
/zie-spec "add rate limiting to API"   ← inline idea (quoted string)

  1. Detect mode:
       - Check `zie-framework/backlog/<arg>.md` exists → **slug mode**
         (existing flow, unchanged — stop here)
       - Arg contains spaces → **quick mode**
       - No backlog file + single word → **quick mode** + warn:
         "No backlog file found for '<arg>' — treating as inline idea."
  2. Print: "Quick spec mode — skipping backlog. Starting spec design..."
  3. Pass idea string to Skill(zie-framework:spec-design) as context
     (same as passing backlog content — idea becomes the problem statement)
  4. spec-design asks clarifying questions, proposes approaches, writes spec,
     runs spec-reviewer loop, records approval in frontmatter
  5. Spec saved to zie-framework/specs/YYYY-MM-DD-<slug>.md
     slug = kebab-case of first 5 words of idea string
  6. ROADMAP Next: add item with spec link (no backlog: field)

/zie-spec <slug>   ← existing slug path (unchanged)
```

**Slug derivation:** kebab-case of first 5 words of idea string.
Example: `"add rate limiting to API"` → `add-rate-limiting-to-api`

**Edge Cases:**

- Idea string is too vague (e.g., `"fix stuff"`) → spec-reviewer will flag and
  reject → user must clarify before proceeding
- Slug collision with existing spec → append `-2`, `-3`, etc.
- User calls `/zie-spec my idea` without quotes → detect multi-word arg with no
  matching backlog file → treat as inline idea with warning
- Reviewer fails 3 iterations → surface to user with partial draft

**Out of Scope:**

- Creating a backlog file as a side effect of quick-spec
- Skipping spec-reviewer (quality gate always runs)
- Generating a plan inline (that is still a separate `/zie-plan` step)
- Parallel quick-specs (one at a time, same as regular flow)
