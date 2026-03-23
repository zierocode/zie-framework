---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-changelog-stale-commands.md
---

# CHANGELOG Stale Command References — Design Spec

**Problem:** `CHANGELOG.md` v1.1.0 section (lines 162–169) references
`/zie-ship` and `/zie-build` which no longer exist, potentially confusing
users who read old release notes.

**Approach:** Annotate the v1.1.0 section with `[REMOVED]` markers on the
affected entries and add a short note pointing to their replacements. The
CHANGELOG remains historical; no entries are deleted.

**Components:**

- `CHANGELOG.md` — annotate v1.1.0 entries for `/zie-ship` and `/zie-build`

**Data Flow:**

1. Locate the v1.1.0 section in `CHANGELOG.md` (line 144 onward).

2. In the `### Changed` block, find the `/zie-ship` entry (around line 163)
   and append `[REMOVED in v1.2.0 → replaced by /zie-release]` inline.

3. Find the `/zie-build` entry (around line 165) — if it references the
   RED/GREEN/REFACTOR steps — and append
   `[REMOVED in v1.2.0 → replaced by /zie-implement]` inline.

4. Exact edits (surgical — no reformatting of surrounding text):

   Before:
   ```markdown
   - **Batch release support** — `[x]` items in the Now lane accumulate pending
     release. `/zie-ship` moves them to Done with a version tag — no need to
     ship features individually.
   ```

   After:
   ```markdown
   - **Batch release support** — `[x]` items in the Now lane accumulate pending
     release. `/zie-ship` moves them to Done with a version tag — no need to
     ship features individually. *(command removed in v1.2.0 — use `/zie-release`)*
   ```

   Before:
   ```markdown
   - **Intent-driven steps** — RED/GREEN/REFACTOR in `/zie-build` are short
     paragraphs instead of bullet micro-steps; config reads collapsed to one
     line.
   ```

   After:
   ```markdown
   - **Intent-driven steps** — RED/GREEN/REFACTOR in `/zie-build` are short
     paragraphs instead of bullet micro-steps; config reads collapsed to one
     line. *(command removed in v1.2.0 — use `/zie-implement`)*
   ```

**Edge Cases:**

- `tests/test_docs_standards.py` has a "CHANGELOG translation" test — verify
  it does not assert exact line content for v1.1.0 entries; if it does,
  update the test assertion
- CHANGELOG must not be reformatted or reordered

**Out of Scope:**

- Adding a formal "Removed" section to v1.1.0 (over-engineering for a
  historical changelog entry)
- Removing the entries entirely
