---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-zieinit-deprecated-filename.md
---

# zie-init Deprecated Filename Reference — Design Spec

**Problem:** `commands/zie-init.md` lines 215 and 219 still reference
`project/decisions.md` in the directory tree diagram, but this file was
renamed to `project/context.md` in v1.3.0.

**Approach:** Replace the two occurrences of `decisions.md` with `context.md`
in the Step 3 directory tree inside `commands/zie-init.md`. No logic changes
needed — only the documentation diagram is wrong.

**Components:**

- `commands/zie-init.md` — fix two stale filename references in the directory
  tree at lines 215 and 219

**Data Flow:**

1. In `commands/zie-init.md` Step 3 directory tree (around line 215), change:

   ```text
   │   └── decisions.md
   ```

   to:

   ```text
   │   └── context.md
   ```

2. Confirm no other occurrences of `project/decisions.md` remain in
   `commands/zie-init.md` (grep check).

3. Verify the rest of `zie-init.md` already uses `project/context.md`
   correctly (lines 87, 231 reference `context.md` — confirmed correct).

**Edge Cases:**

- `templates/` directory: `templates/project/` should contain
  `context.md.template`, not `decisions.md.template` — verify separately
  (out of scope for this spec, but flag if wrong)
- Tests in `tests/test_docs_standards.py` may assert filename references —
  run test suite after fix to confirm no regressions

**Out of Scope:**

- Renaming any actual files (already done in v1.3.0)
- Updating CHANGELOG entry for v1.3.0 (already documented there)
