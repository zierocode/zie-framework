---
slug: lean-fix-hotfix-triage-rule
approved: true
approved_at: 2026-04-04
---

# lean-fix-hotfix-triage-rule — Design Spec

**Problem:** /fix and /hotfix have overlapping one-line descriptions with no
decision signal. Users cannot tell from the description alone which command
to use, so they guess — causing /hotfix to be used for non-urgent bugs
(unnecessary release churn) or /fix to be used for prod incidents (no
immediate release triggered).

**Approach:** Append a single triage sentence to the opening description of
each command file, and mirror the same distinction in the PROJECT.md Commands
table description column. No structural changes, no new sections, no tests
required (doc-only).

**Components:**

- `commands/fix.md` — append triage sentence to description line
- `commands/hotfix.md` — append triage sentence to description line
- `zie-framework/PROJECT.md` — update Commands table description column for
  `/fix` and `/hotfix` rows

**Exact Changes:**

Triage sentence for `commands/fix.md` (append to opening description):

> Use for non-urgent bugs. Does not trigger an immediate release.

Triage sentence for `commands/hotfix.md` (append to opening description):

> Use only for prod incidents requiring immediate release. Triggers release gate automatically. For non-urgent bugs, use /fix instead.

**Data Flow:**

1. User reads `/fix` or `/hotfix` description
2. Triage sentence immediately signals urgency requirement and release consequence
3. Wrong-command reference directs user to the correct alternative

**Edge Cases:**

- `commands/fix.md` or `commands/hotfix.md` may have multiline preambles —
  the sentence must be appended to the description block, not mid-step
- PROJECT.md Commands table cell widths may need minor adjustment for the
  longer text; no functional impact
- No frontmatter changes required in either command file

**Out of Scope:**

- Structural changes (new sections, new headings, decision tables)
- Changes to step logic, test requirements, or release gate behaviour
- Changes to any hook or skill files
- Adding examples or diagrams
