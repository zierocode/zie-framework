---
slug: audit-project-md-docs-sync
status: approved
approved: true
date: 2026-04-01
---

# Plan: audit-project-md-docs-sync

## Summary

Add the missing `docs-sync-check` skill row to the Skills table in
`zie-framework/PROJECT.md`. One targeted line edit. No new files, no hook or
command changes, no test changes.

## Source Spec

`zie-framework/specs/2026-04-01-audit-project-md-docs-sync-design.md`

---

## Tasks

### Task 1 — Add `docs-sync-check` row to PROJECT.md Skills table

**File:** `zie-framework/PROJECT.md`

**Exact edit — append one row after the last row of the Skills table:**

Before:
```
| `sprint-planner` | Batch spec + plan + implement + release + retro |
```

After:
```
| `sprint-planner` | Batch spec + plan + implement + release + retro |
| `docs-sync-check` | Verify PROJECT.md is in sync with repo state — skills, hooks, commands, templates |
```

The description is derived directly from `skills/docs-sync-check/SKILL.md`
(Purpose field), trimmed to one clause for table width.

---

## Verification

### Step 1 — grep confirmation

```bash
grep -n "docs-sync-check" zie-framework/PROJECT.md
```

Expected: exits 0, prints exactly one line containing `docs-sync-check`.

### Step 2 — row content sanity check

The printed line must contain both `docs-sync-check` and a description that
matches the skill's stated purpose ("in sync with repo state").

---

## Test Strategy

- **No new tests required.** This is a documentation-only change.
- **Existing suite must pass.** Run `make test-fast` after the edit to confirm
  no tests were broken.

---

## Rollout

1. Read current `zie-framework/PROJECT.md`.
2. Apply str_replace: append the `docs-sync-check` table row after `sprint-planner`.
3. Run verification grep — confirm exit 0 and correct line.
4. Run `make test-fast` — confirm all tests green.
5. Mark task complete in ROADMAP.md.

**Estimated effort:** < 5 minutes. Single str_replace, one grep, one test run.

**Risk:** None. Additive change to a Markdown table. No runtime code touched.
