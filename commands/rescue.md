---
description: Diagnose current pipeline position and show next action — read-only, never modifies state.
argument-hint: ""
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
effort: low
---

# /rescue — Pipeline Diagnosis

<!-- preflight: minimal -->

Scan zie-framework artifacts to determine where you are in the pipeline
and what to do next. Read-only — no side effects.

## Steps

1. **Check prerequisites**
   - If `zie-framework/` absent → print "Not initialized — run /init first." Stop.

2. **Scan backlog items**
   - Glob `zie-framework/backlog/*.md` → list filenames (slugs)
   - For each slug: check if corresponding spec + plan exist

3. **Build pipeline state per slug**

   For each backlog slug:
   - `spec`: Glob `zie-framework/specs/*-<slug>-design.md` — read `approved:` frontmatter
   - `plan`: Glob `zie-framework/plans/*-<slug>.md` — read `approved:` frontmatter
   - `impl`: Check if slug appears in ROADMAP.md Now lane (→ in progress)
   - `released`: Check if slug appears in ROADMAP.md Done lane

4. **Determine active feature**
   - ROADMAP Now lane — extract current slug
   - If empty: find slug with approved plan but not in Done
   - If none found: no active pipeline

5. **Print diagnosis**

   For active feature:
   ```
   /rescue — pipeline diagnosis

   Feature: <slug>

   ✅ backlog:   present
   ✅ spec:      approved (<date>)
   ✅ plan:      approved (<date>)
   🔄 implement: in progress
   ⬜ release:   pending
   ⬜ retro:     pending

   → Next: <specific action based on state>
   ```

   State → Next action mapping:
   - No spec → `Run /spec <slug>`
   - Spec not approved → `Run Skill(zie-framework:spec-reviewer) then python3 hooks/approve.py <spec-path>`
   - No plan → `Run /plan <slug>`
   - Plan not approved → `Run Skill(zie-framework:plan-reviewer) then python3 hooks/approve.py <plan-path>`
   - Plan approved, not in Now → `Run /implement`
   - In Now lane → `Run make test-fast to continue implementation`
   - Tests failing → `Run make test-fast — fix failing tests, then /release`

6. **Multiple features in progress**
   - If multiple slugs found with partial pipeline state → list all with their stage
   - Ask: "Which feature do you want to rescue?"

7. **No active pipeline**
   - Print: "No active pipeline detected. Run /brainstorm or /backlog to start."

## Error Handling

- Git command fails: omit git state from report, continue
- Artifact file unreadable: mark that step as `⬜ unknown`, continue
- ROADMAP unreadable: skip Now/Done lane checks

→ /implement to resume, or /fix to debug
- Always exits cleanly — never halts or prompts for confirmation
