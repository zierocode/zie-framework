---
approved: false
approved_at:
backlog: backlog/roadmap-done-rotation.md
---

# ROADMAP Done-Section Rotation — Implementation Plan

**Goal:** Add an inline Done-rotation step to `commands/zie-retro.md` that archives Done items older than 90 days into per-month archive files, always keeping the 10 most-recent items inline.
**Architecture:** Pure command file edit — no new Python files, no new agents, no new skills. Claude executes the rotation inline after the ROADMAP-update agent completes. The step reads the Done section, applies date-extraction + keep-10 + 90-day-threshold rules, writes the updated ROADMAP.md, and appends to per-month archive files under `zie-framework/archive/`.
**Tech Stack:** Markdown (commands/zie-retro.md), Claude inline execution

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-retro.md` | Add Done-rotation inline step after ROADMAP-update agent await; extend auto-commit git add to include ROADMAP.md and archive files |

---

## Task Sizing

Plan size: S (2 tasks — single command file edit + AC verification)

---

## Task 1: Add Done-Rotation Inline Step to zie-retro.md

**Acceptance Criteria:**
- `commands/zie-retro.md` contains an inline Done-rotation step positioned immediately after the ROADMAP-update agent await (`Await both`) and before the `### Auto-commit retro outputs` section
- The step includes: date-extraction logic (scan item text for all `YYYY-MM-DD` occurrences, take last match), 90-day threshold check, keep-10-most-recent rule (by extracted date descending; no-date items sort last), archive path formula `zie-framework/archive/ROADMAP-archive-YYYY-MM.md` (YYYY-MM from item's extracted date), append-only write guard (create with header if file absent; append new section if file exists — never truncate), no-date-keep rule, ≤10 early-exit guard
- No `Agent(` call wraps the rotation logic (inline step only)
- The auto-commit step's `git add` line includes `zie-framework/ROADMAP.md` and `zie-framework/archive/ROADMAP-archive-*.md`

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing test (RED)**
  Verify the rotation step is NOT yet present:
  ```bash
  grep -n "Done-rotation" /Users/zie/Code/zie-framework/commands/zie-retro.md
  ```
  Expected: no output (step absent — RED state confirmed).

- [ ] **Step 2: Implement (GREEN)**

  Read `commands/zie-retro.md` to locate the exact insertion point, then apply two edits:

  **Edit A — Insert Done-rotation step** between `Await both. Then proceed to brain store.` and `### Auto-commit retro outputs`:

  Insert the following block (as new Markdown section) after `Await both. Then proceed to brain store.` and before `**Failure mode:**`:

  ```markdown
  ### Done-rotation (inline)

  After ROADMAP-update agent completes, apply Done-rotation inline — no Agent call:

  1. Read the current `## Done` section of `zie-framework/ROADMAP.md`.
  2. **Early-exit guard:** if Done section contains ≤ 10 items → skip rotation entirely, no archive file written.
  3. **Date extraction:** for each Done item, scan the item text for all `YYYY-MM-DD` patterns; take the **last** match as the item's canonical date. Items with no parseable date are treated as "recent" (kept inline, never archived).
  4. **Sort:** rank items by extracted date descending; items with no date sort last.
  5. **Keep rule:** always keep the 10 most-recent items (by extracted date) inline, regardless of age.
  6. **Threshold:** an item is a candidate for archival when `today − item_date > 90 days`. Items with no date are never archived.
  7. **Candidates:** items ranked 11+ with an extracted date > 90 days old are archive candidates.
  8. **Archive write (append-only):** for each candidate, determine archive path: `zie-framework/archive/ROADMAP-archive-YYYY-MM.md` where `YYYY-MM` is derived from the item's own extracted date.
     - If file does not exist → create it with header:
       ```markdown
       # ROADMAP Archive — YYYY-MM

       <!-- Archived from zie-framework/ROADMAP.md by /zie-retro. Append-only. -->
       ```
     - Append a new section (never rewrite or truncate existing content):
       ```markdown
       ## Archived YYYY-MM-DD

       - [x] <original item text, verbatim>
       ```
       Where `YYYY-MM-DD` in the heading is today's date (archival timestamp). Group all items sharing the same archive month under a single heading.
  9. **ROADMAP update:** rewrite the `## Done` section to contain only the 10 kept items (preserving original text verbatim).
  10. Print: `Done-rotation: kept <N>, archived <M> items to <K> file(s)` — or `Done-rotation: ≤10 items, skipped` on early-exit.
  ```

  **Edit B — Extend auto-commit git add** in `### Auto-commit retro outputs`:

  Change:
  ```bash
  git add zie-framework/decisions/*.md zie-framework/project/components.md
  ```
  To:
  ```bash
  git add zie-framework/decisions/*.md zie-framework/project/components.md zie-framework/ROADMAP.md zie-framework/archive/ROADMAP-archive-*.md
  ```

- [ ] **Step 3: Refactor**
  Review the inserted step for prose clarity and consistency with surrounding section style (Thai section headers, inline code blocks). No logic changes needed.

---

## Task 2: Verify Acceptance Criteria

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- All 8 ACs from the spec are satisfied as verified by read/grep

**Files:**
- Read: `commands/zie-retro.md`

- [ ] **Step 1: Verify rotation step placement (AC-8)**
  ```bash
  grep -n "Done-rotation" /Users/zie/Code/zie-framework/commands/zie-retro.md
  ```
  Expected: line present, positioned after ROADMAP-update agent await and before auto-commit.

- [ ] **Step 2: Verify no Agent( wraps rotation (AC-8)**
  Confirm the rotation section contains no `Agent(` call:
  ```bash
  grep -A 40 "Done-rotation (inline)" /Users/zie/Code/zie-framework/commands/zie-retro.md | grep "Agent("
  ```
  Expected: no output.

- [ ] **Step 3: Verify key logic elements present (AC-1 through AC-6)**
  Read `commands/zie-retro.md` and confirm the rotation step contains:
  - `≤ 10 items` early-exit guard (AC-5)
  - `YYYY-MM-DD` date-extraction logic, last match (spec date detection rule)
  - `90 days` threshold (AC-2)
  - `10 most-recent` keep rule (AC-6)
  - `archive/ROADMAP-archive-YYYY-MM.md` path formula (AC-2)
  - Append-only write guard — "never rewrite or truncate" (AC-3)
  - No-date items kept inline (AC-4)

- [ ] **Step 4: Verify extended git add (AC-7)**
  ```bash
  grep "archive/ROADMAP-archive" /Users/zie/Code/zie-framework/commands/zie-retro.md
  ```
  Expected: line present inside the auto-commit section.

- [ ] **Step 3: Refactor**
  No refactor needed for a verification task.
