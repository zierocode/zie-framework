# Spec: ROADMAP Done-Section Rotation — Inline Archival Step in /zie-retro

Date: 2026-04-04
Status: Draft
Author: Zie

---

## Problem

The `## Done` section of `zie-framework/ROADMAP.md` grows unboundedly. Every release
appends one or more items; nothing removes them. Over time the section becomes too long
to scan quickly and bloats every ROADMAP read in `/zie-status`, `/zie-retro`, and
planning commands. There is currently no mechanism to move stale Done items out of the
active file.

---

## Goal

After each `/zie-retro` run, automatically rotate Done items that are older than 90 days
into per-month archive files. Always keep the 10 most-recent Done items inline so recent
history stays visible. Archive is append-only.

---

## Approach — Dedicated Inline Step in /zie-retro (Option C)

Add a single inline step **immediately after the ROADMAP-update agent completes** (before
auto-commit). Claude reads the Done section, applies the rotation rules, and writes the
updated ROADMAP plus any archive files directly — no new agent spawned.

### Trigger

Runs as an inline step in `/zie-retro`, after the ROADMAP-update agent completes and
before the auto-commit step.

### Date Detection

Done items may contain dates in either of two patterns:

| Pattern | Example |
| --- | --- |
| `v<X.Y.Z> YYYY-MM-DD` | `v1.16.2 2026-04-03` |
| Bare `YYYY-MM-DD` | `2026-04-03` |

Extraction rule: scan the item text for **all** `YYYY-MM-DD` occurrences; take the
**last** match as the item's canonical date.

Items with no parseable `YYYY-MM-DD` are treated as "recent" and kept inline. Ambiguous
items are never archived.

### Threshold

An item is a **candidate for archival** when:

```
today − item_date > 90 days
```

Today's date is determined at runtime (same session date used throughout `/zie-retro`).

### Keep Rule

Always keep the **10 most-recent** Done items inline, regardless of age. Recency is
determined by extracted date (descending); items with no date sort last (kept inline).

If the Done section contains ≤ 10 items total, no rotation occurs — exit the step early.

### Archive File

- Path: `zie-framework/archive/ROADMAP-archive-YYYY-MM.md`
- `YYYY-MM` is derived from the **item's own extracted date** (not today).
- Items from different months go to different archive files.

### Archive Format

Archive files are **append-only**:

1. If the file does not exist → create it with a header, then append the item(s).
2. If the file already exists → append a new section after existing content.
   **Never rewrite or truncate existing archive content.**

Archive file structure:

```markdown
# ROADMAP Archive — YYYY-MM

<!-- Archived from zie-framework/ROADMAP.md by /zie-retro. Append-only. -->

## Archived YYYY-MM-DD

- [x] <original item text, verbatim>
```

When multiple items share the same archive month, group them under a single
`## Archived YYYY-MM-DD` heading (using today's date as the archival timestamp).

### Execution Order

```
ROADMAP-update agent completes
      ↓
[NEW] Done-rotation inline step
      ↓
auto-commit  (picks up ROADMAP.md + any new archive files)
```

The auto-commit step already stages `zie-framework/decisions/*.md` and
`zie-framework/project/components.md`. Extend staging to include:

```bash
git add zie-framework/ROADMAP.md zie-framework/archive/ROADMAP-archive-*.md
```

---

## Files Changed

| File | Change |
| --- | --- |
| `commands/zie-retro.md` | Add inline Done-rotation step between "await ROADMAP-update agent" and "auto-commit"; extend `git add` in auto-commit to include ROADMAP.md and archive files |

No new Python files. No new agent calls. No skill changes.

---

## Acceptance Criteria

| # | AC |
| --- | --- |
| AC-1 | After `/zie-retro` runs, the `## Done` section of `zie-framework/ROADMAP.md` contains at most 10 items. Verify by reading the file after a retro run that had > 10 Done items. |
| AC-2 | Items with an extracted date > 90 days before today are moved to the correct `zie-framework/archive/ROADMAP-archive-YYYY-MM.md` file (YYYY-MM derived from the item's own date). |
| AC-3 | Archive files are append-only: if `ROADMAP-archive-YYYY-MM.md` already exists, new items are appended as a new section; no existing content is overwritten. |
| AC-4 | Items with no parseable `YYYY-MM-DD` date remain inline and are never archived. |
| AC-5 | If Done section has ≤ 10 items, the rotation step exits early and no archive file is written. |
| AC-6 | The 10 most-recent items (by extracted date, descending) always remain inline even if they are older than 90 days. |
| AC-7 | The auto-commit step stages `zie-framework/ROADMAP.md` and `zie-framework/archive/ROADMAP-archive-*.md` in addition to the existing paths. |
| AC-8 | The rotation step runs inline (no new `Agent(` call added for this step). Verify by reading `commands/zie-retro.md` and confirming no Agent call wraps the rotation logic. |

---

## Testing

Not applicable — this is a command file change (Markdown). No Python code is added or
modified; no pytest tests exist for command prose.

AC verification method: read `commands/zie-retro.md` after implementation and confirm:

- Inline Done-rotation step present between ROADMAP-update agent await and auto-commit
- Step includes: date-extraction logic (last `YYYY-MM-DD` match), 90-day threshold,
  keep-10-most-recent rule, archive path formula `archive/ROADMAP-archive-YYYY-MM.md`,
  append-only write guard, no-date-keep rule, ≤10 early-exit guard
- `git add` in auto-commit includes `zie-framework/ROADMAP.md` and
  `zie-framework/archive/ROADMAP-archive-*.md`
- No `Agent(` call wraps the rotation logic

---

## Out of Scope

- Archiving items from `## Next`, `## Now`, or `## Backlog` sections
- Rotating archive files themselves (archive files are permanent)
- The existing `make archive-prune` step (prunes `archive/` files >90 days — orthogonal;
  archive ROADMAP files should be excluded from prune or the prune threshold should be
  reviewed separately)
- Changing the Done-item date format
- Adding a CLI or Make target for standalone rotation
