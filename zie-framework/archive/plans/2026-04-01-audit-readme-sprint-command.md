---
slug: audit-readme-sprint-command
status: approved
approved: true
date: 2026-04-01
---

# Plan: Add /zie-sprint to README Commands Table

## Overview

Single-task plan. One row is inserted into the README.md commands table,
directly after the `/zie-retro` row. No logic changes.

## Spec

`zie-framework/specs/2026-04-01-audit-readme-sprint-command-design.md`

---

## Tasks

### Task 1 — Insert `/zie-sprint` row into README.md commands table

**File:** `README.md`

**Before:**

```markdown
| `/zie-retro` | Post-release retrospective + ADRs |
| `/zie-fix` | Debug and fix failing tests or broken features |
```

**After:**

```markdown
| `/zie-retro` | Post-release retrospective + ADRs |
| `/zie-sprint` | Sprint clear — batch all items: spec + plan + implement + release + retro |
| `/zie-fix` | Debug and fix failing tests or broken features |
```

**Method:** Use str_replace on the exact line `| \`/zie-retro\` | Post-release retrospective + ADRs |` to append the new row immediately after it.

---

## Verification

After editing, run:

```bash
grep '/zie-sprint' README.md
```

Expected output:

```
| `/zie-sprint` | Sprint clear — batch all items: spec + plan + implement + release + retro |
```

If the grep returns no match, the edit failed — abort and re-apply.

---

## Test Strategy

This change is documentation-only. No application logic is modified.

- Run `make test-ci` after the edit to confirm the full test suite still passes.
- The markdown linter (part of `make test`) will catch any table formatting errors.
- No new tests are required for this change.
- Pyramid level: N/A (no code changed). Verification is a grep assertion.

---

## Rollout

1. Apply Task 1 (str_replace in README.md).
2. Run verification grep.
3. Run `make test-ci` — must pass before marking complete.
4. Mark backlog item `audit-readme-sprint-command` status: done.
5. Move ROADMAP item to Done lane.
