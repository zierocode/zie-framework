---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-fix-hotfix-triage-rule.md
---

# lean-fix-hotfix-triage-rule — Implementation Plan

**Goal:** Append exact triage sentences to `/fix` and `/hotfix` command descriptions, and update the PROJECT.md Commands table, so users immediately know which command to reach for.
**Architecture:** Doc-only edits to three files — two command frontmatter descriptions and one Markdown table row. No code, no hooks, no tests needed.
**Tech Stack:** Markdown, Edit tool.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/fix.md` | Append triage sentence to `description` frontmatter field |
| Modify | `commands/hotfix.md` | Append triage sentence to `description` frontmatter field |
| Modify | `zie-framework/PROJECT.md` | Extend `/fix` and `/hotfix` rows in Commands table |

---

## Task 1: Add triage sentence to commands/fix.md

**Acceptance Criteria:**
- The `description` field in `commands/fix.md` frontmatter ends with: `Use for non-urgent bugs. Does not trigger an immediate release.`
- All other content in the file is unchanged.

**Files:**
- Modify: `commands/fix.md`

- [ ] **Step 1: Write failing tests (RED)**

  Doc-only change — no automated tests. Manual verification is the test:

  ```bash
  grep "Use for non-urgent bugs" /Users/zie/Code/zie-framework/commands/fix.md
  ```

  Expected: no match (confirms the sentence is not yet present before edit).

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/fix.md` frontmatter — change:

  ```yaml
  description: Debug path — skip ideation, go straight to systematic bug investigation and fix.
  ```

  to:

  ```yaml
  description: Debug path — skip ideation, go straight to systematic bug investigation and fix. Use for non-urgent bugs. Does not trigger an immediate release.
  ```

  Verify:

  ```bash
  grep "Use for non-urgent bugs" /Users/zie/Code/zie-framework/commands/fix.md
  ```

  Expected output:
  ```
  description: Debug path — skip ideation, go straight to systematic bug investigation and fix. Use for non-urgent bugs. Does not trigger an immediate release.
  ```

- [ ] **Step 3: Refactor**

  No refactor needed. Confirm no other lines were changed:

  ```bash
  git diff commands/fix.md
  ```

---

## Task 2: Add triage sentence to commands/hotfix.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- The `description` field in `commands/hotfix.md` frontmatter ends with: `Use only for prod incidents requiring immediate release. Triggers release gate automatically. For non-urgent bugs, use /fix instead.`
- All other content in the file is unchanged.

**Files:**
- Modify: `commands/hotfix.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```bash
  grep "Use only for prod incidents" /Users/zie/Code/zie-framework/commands/hotfix.md
  ```

  Expected: no match.

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/hotfix.md` frontmatter — change:

  ```yaml
  description: Emergency fix track — describe → fix → ship without full pipeline
  ```

  to:

  ```yaml
  description: Emergency fix track — describe → fix → ship without full pipeline. Use only for prod incidents requiring immediate release. Triggers release gate automatically. For non-urgent bugs, use /fix instead.
  ```

  Verify:

  ```bash
  grep "Use only for prod incidents" /Users/zie/Code/zie-framework/commands/hotfix.md
  ```

  Expected output:
  ```
  description: Emergency fix track — describe → fix → ship without full pipeline. Use only for prod incidents requiring immediate release. Triggers release gate automatically. For non-urgent bugs, use /fix instead.
  ```

- [ ] **Step 3: Refactor**

  ```bash
  git diff commands/hotfix.md
  ```

  Confirm only the description line changed.

---

## Task 3: Update PROJECT.md Commands table

<!-- depends_on: none -->

**Acceptance Criteria:**
- The `/fix` row in the PROJECT.md Commands table includes: `Use for non-urgent bugs. Does not trigger an immediate release.`
- The `/hotfix` row is added (or updated) with: `Use only for prod incidents requiring immediate release. Triggers release gate automatically.`
- Table renders correctly in Markdown.

**Files:**
- Modify: `zie-framework/PROJECT.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```bash
  grep "non-urgent bugs" /Users/zie/Code/zie-framework/zie-framework/PROJECT.md
  ```

  Expected: no match.

- [ ] **Step 2: Implement (GREEN)**

  Edit the Commands table in `zie-framework/PROJECT.md`.

  Change the `/fix` row from:

  ```markdown
  | /fix | Bug → regression test → fix → verify |
  ```

  to:

  ```markdown
  | /fix | Bug → regression test → fix → verify. Use for non-urgent bugs. Does not trigger an immediate release. |
  ```

  Add `/hotfix` row after `/fix` (if not already present):

  ```markdown
  | /hotfix | Emergency fix → ship without full pipeline. Use only for prod incidents requiring immediate release. Triggers release gate automatically. |
  ```

  Verify:

  ```bash
  grep -E "/fix|/hotfix" /Users/zie/Code/zie-framework/zie-framework/PROJECT.md
  ```

  Expected output includes both rows with triage text.

- [ ] **Step 3: Refactor**

  ```bash
  git diff zie-framework/PROJECT.md
  ```

  Confirm only the Commands table rows for `/fix` and `/hotfix` changed.
