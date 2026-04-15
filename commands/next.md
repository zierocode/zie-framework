---
description: Rank backlog items by impact, age, and dependencies — recommend top 3 with reasoning.
argument-hint: ""
allowed-tools: Read, Glob, Grep
model: sonnet
effort: low
---

# /next — Recommended Next Backlog Items

Read-only. Scans `zie-framework/backlog/`, scores items, and recommends top 3.

<!-- preflight: minimal -->

## Steps

1. **Check prerequisites**
   - If `zie-framework/` absent → print "Not initialized — run /init first." Stop.

2. **Scan backlog items**
   - Glob `zie-framework/backlog/*.md` — read each file
   - Extract per item:
     - `title`: first non-frontmatter heading or filename slug
     - `impact`: frontmatter `impact:` field (high/medium/low) — default `medium` if absent
     - `created`: frontmatter `created:` field (ISO date) — default today if absent
     - `depends_on`: frontmatter `depends_on:` list — slugs of blocking items

3. **Filter in-progress items**
   - For each slug: Glob `zie-framework/specs/*-<slug>-design.md` → read `approved:` field
   - If `approved: true` → item is in pipeline — EXCLUDE from ranking
   - If in ROADMAP.md Now lane → EXCLUDE

4. **Score remaining items**

   For each item:
   ```
   impact_score = high→3, medium→2, low→1
   age_weeks = (today - created_date).days // 7
   age_score = min(age_weeks, 5)     # cap at 5 weeks
   dep_penalty = -2 × count(unresolved_depends_on)
   total = impact_score + age_score + dep_penalty
   ```

5. **Rank by total score (descending)**

6. **Print top 3**

   ```
   /next

   1. [HIGH] conversation-capture (score:7) age:3d | /spec conversation-capture
   2. [MEDIUM] code-quality-gates (score:4) age:1w | /spec code-quality-gates
   3. [LOW] adaptive-learning (score:2) age:0d | /spec adaptive-learning
   ```

7. **Edge cases**

   - Empty backlog → "No backlog items. Run /brainstorm or /backlog to start."
   - All items in progress → "All backlog items are in pipeline. Run /rescue for status."
   - < 3 items → show what's available (no padding)
   - Malformed backlog file → skip that item, continue
   - Missing `created:` field → treat as age = 0 (no age bonus)

## Error Handling

- Backlog file unreadable: skip, continue to next item
- Spec glob fails: assume item not in pipeline
- Date parse error: treat age as 0
- Always exits cleanly — never halts or modifies anything

→ /spec <slug> to start the pipeline
