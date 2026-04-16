---
description: Turn a backlog item into a written spec with Acceptance Criteria. Second stage of the SDLC pipeline.
argument-hint: "[slug|\"idea\"] — backlog slug or inline idea string (e.g. /spec add-csv-export OR /spec \"add rate limiting\")"
allowed-tools: Read, Write, Edit, Bash, Glob, Skill
model: sonnet
effort: medium
---

# /spec — Backlog → Spec

<!-- preflight: full -->

Write a design spec for a backlog item. Invokes spec-design skill with
reviewer loop. Output lives in `zie-framework/specs/`.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (checks Now lane — warns if WIP active).

## Arguments

| Flag | Description | Default |
| --- | --- | --- |
| `--draft-plan` | After spec is approved, auto-invoke `zie-framework:write-plan` and move plan to Ready if approved. Skips manual `/plan` step. | off |

## Context Bundle

<!-- context-load: adrs + project context -->

Extract keywords from backlog item (Problem + Approach sections — split on whitespace, remove stop words, take top 6 unique terms).
Invoke `Skill(zie-framework:context, '<keywords>')` → result available as `context_bundle`.
Pass `context_bundle` to spec-design and spec-review invocations.

## Steps

1. **Detect input mode:**

   - If arg is provided:
     - Check `zie-framework/backlog/<arg>.md` exists → **slug mode**: read
       backlog file → continue to step 2.
     - Arg contains spaces → **quick mode**: go to quick-spec flow (step 3).
     - No backlog file + single word → **quick mode** + warn: "No backlog
       file found for '`<arg>`' — treating as inline idea."
   - If no arg → read ROADMAP.md Next section, list items, ask: "Which to
     spec? Enter number." → slug mode.

2. **Slug mode** (existing flow): pass backlog file content to
   `Skill(zie-framework:spec-design)` with `context_bundle` and `zie_memory_enabled` from
   .config.
   Spec saved to `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`
   with `approved: true` in frontmatter once reviewed.

   Commit spec after approval:

   ```bash
   git add zie-framework/specs/YYYY-MM-DD-<slug>-design.md
   git commit -m "spec: <slug>"
   ```

   Go to step 4.

3. **Quick spec mode** (new): print "Quick spec mode — skipping backlog.
   Starting spec design..."

   - Derive slug: kebab-case of first 5 words of idea string.
     Example: `"add rate limiting to API"` → `add-rate-limiting-to-api`
   - Check slug collision: if `zie-framework/specs/*-<slug>-design.md`
     already exists → append `-2`, `-3`, etc.
   - Pass idea string directly to `Skill(zie-framework:spec-design)` with `context_bundle` as
     context (idea string becomes the problem statement — no backlog file
     needed).
   - spec-design asks clarifying questions, proposes approaches, writes
     spec, runs spec-review once, fixes issues inline if any, records `approved: true` in frontmatter.
   - After spec approved, add to ROADMAP Next:
     `- [ ] <idea title> — [spec](specs/YYYY-MM-DD-<slug>-design.md)`

   Commit spec + ROADMAP after approval:

   ```bash
   git add zie-framework/specs/YYYY-MM-DD-<slug>-design.md \
     zie-framework/ROADMAP.md
   git commit -m "spec: <slug>"
   ```

4. **--draft-plan branch** (if `--draft-plan` present — remove flag from slug before processing):

   After spec commit:
   1. Auto-invoke `Skill(zie-framework:write-plan)` with slug → plan written with `approved: false`
   2. Invoke `Skill(zie-framework:review, 'phase=plan')` inline with plan path + spec path
   3. If ✅ APPROVED → run approve.py via Bash (reviewer-gate blocks Write/Edit — this is the only allowed path):
      ```bash
      python3 hooks/approve.py zie-framework/plans/YYYY-MM-DD-<slug>.md
      ```
      Move ROADMAP Next → Ready, commit
   - Combined handoff:
     ```text
     Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md
     Plan approved ✓ → zie-framework/plans/YYYY-MM-DD-<slug>.md
                       ROADMAP: <slug> moved Next → Ready

     Next: /implement <slug>
     ```
   - On plan ISSUES: spec remains approved; print "Address plan issues and re-run: /plan <slug>"

5. Print handoff (no `--draft-plan` flag):

   ```text
   Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: /plan <slug> to create the implementation plan.
   ```

