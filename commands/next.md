---
description: Rank backlog items by impact, age, and dependencies — recommend top 3 with reasoning. Supports --rescue for pipeline diagnosis.
argument-hint: "[--rescue]"
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
effort: low
---

# /next — Recommended Next Backlog Items

<!-- preflight: minimal -->

Read-only. Scans `zie-framework/backlog/`, scores items, and recommends top 3.

Supports `--rescue` flag for pipeline diagnosis (merged from /rescue).

## Steps

1. **Parse flags** — check `$ARGUMENTS` for `--rescue`.

### If --rescue — Pipeline Diagnosis

2. **Check prerequisites**
   - If `zie-framework/` absent → print "Not initialized — run /init first." Stop.

3. **Scan backlog items**
   - Glob `zie-framework/backlog/*.md` → list filenames (slugs)
   - For each slug: check if corresponding spec + plan exist

4. **Build pipeline state per slug**

   For each backlog slug:
   - `spec`: Glob `zie-framework/specs/*-<slug>-design.md` — read `approved:` frontmatter
   - `plan`: Glob `zie-framework/plans/*-<slug>.md` — read `approved:` frontmatter
   - `impl`: Check if slug appears in ROADMAP.md Now lane (→ in progress)
   - `released`: Check if slug appears in ROADMAP.md Done lane

5. **Determine active feature**
   - ROADMAP Now lane — extract current slug
   - If empty: find slug with approved plan but not in Done
   - If none found: no active pipeline

6. **Print diagnosis**

   For active feature:
   ```
   /next --rescue — pipeline diagnosis

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
   - Spec not approved → `Run Skill(zie-framework:spec-review) then python3 hooks/approve.py <spec-path>`
   - No plan → `Run /plan <slug>`
   - Plan not approved → `Run Skill(zie-framework:review, 'phase=plan') then python3 hooks/approve.py <plan-path>`
   - Plan approved, not in Now → `Run /implement`
   - In Now lane → `Run make test-fast to continue implementation`
   - Tests failing → `Run make test-fast — fix failing tests, then /release`

7. **Multiple features in progress**
   - If multiple slugs found with partial pipeline state → list all with their stage
   - Ask: "Which feature do you want to rescue?"

8. **No active pipeline**
   - Print: "No active pipeline detected. Run /backlog to start."

   Stop.

### Default — Rank backlog items

2. **Check prerequisites**
   - If `zie-framework/` absent → print "Not initialized — run /init first." Stop.

3. **Scan backlog items**
   - Glob `zie-framework/backlog/*.md` — read each file
   - Extract per item:
     - `title`: first non-frontmatter heading or filename slug
     - `impact`: frontmatter `impact:` field (high/medium/low) — default `medium` if absent
     - `created`: frontmatter `created:` field (ISO date) — default today if absent
     - `depends_on`: frontmatter `depends_on:` list — slugs of blocking items

4. **Filter in-progress items**
   - For each slug: Glob `zie-framework/specs/*-<slug>-design.md` → read `approved:` field
   - If `approved: true` → item is in pipeline — EXCLUDE from ranking
   - If in ROADMAP.md Now lane → EXCLUDE

5. **Score remaining items**

   For each item:
   ```
   impact_score = high→3, medium→2, low→1
   age_weeks = (today - created_date).days // 7
   age_score = min(age_weeks, 5)     # cap at 5 weeks
   dep_penalty = -2 × count(unresolved_depends_on)
   total = impact_score + age_score + dep_penalty
   ```

6. **Rank by total score (descending)**

7. **Print top 3**

   ```
   /next

   1. [HIGH] conversation-capture (score:7) age:3d | /spec conversation-capture
   2. [MEDIUM] code-quality-gates (score:4) age:1w | /spec code-quality-gates
   3. [LOW] adaptive-learning (score:2) age:0d | /spec adaptive-learning
   ```

8. **Edge cases**

   - Empty backlog → "No backlog items. Run /backlog to start."
   - All items in progress → "All backlog items are in pipeline. Run /next --rescue for status."
   - < 3 items → show what's available (no padding)
   - Malformed backlog file → skip that item, continue
   - Missing `created:` field → treat age as 0 (no age bonus)

## Error Handling

- Backlog file unreadable: skip, continue to next item
- Spec glob fails: assume item not in pipeline
- Date parse error: treat age as 0
- Git command fails: omit git state from rescue report, continue
- Artifact file unreadable: mark that step as `⬜ unknown`, continue
- Always exits cleanly — never halts or modifies anything

→ /spec <slug> to start the pipeline