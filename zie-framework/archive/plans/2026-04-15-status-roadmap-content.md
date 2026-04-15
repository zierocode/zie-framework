---
date: 2026-04-15
status: approved
slug: status-roadmap-content
---

# Implementation Plan — status-roadmap-content

## Steps

1. **Read backlog excerpts in `/status`** — After step 2 (read files), for each slug in Now and Ready lanes (from `parse_roadmap_section`), read `zie-framework/backlog/<slug>.md`. Extract text between `## Problem` and the next `##` heading. Truncate to first 120 characters, append ellipsis if longer. If file missing or no Problem section, show `(no description)`.

2. **Read spec/plan existence** — For each slug, check `zie-framework/specs/*-<slug>-design.md` and `zie-framework/plans/*-<slug>.md`. Record existence only (no content read).

3. **Update step 7 output** — After the ROADMAP summary block, add a "Pipeline Detail" section:

   ```
   **Pipeline Detail**
   - init-scaffold-claude-code-config: Scaffold .claude/ config during /init … | spec ✓ plan —
   - backlog-dedup-expand: Dedup check against Done items and expand … | spec ✓ plan ✓
   ```

   One line per Now/Ready item: `<slug>: <excerpt> | spec <✓|—> plan <✓|—>`.

4. **Gate on Now+Ready only** — Skip this section if both Now and Ready lanes are empty.

## Tests

1. **Unit: extract problem excerpt** — Given a backlog markdown file with `## Problem\nSome text\n\n## Rough Scope`, verify the excerpt is "Some text" truncated at 120 chars.
2. **Unit: missing backlog file** — Verify `(no description)` is returned for nonexistent slug.
3. **Unit: spec/plan detection** — Verify correct ✓/— for present/absent spec and plan files.
4. **Integration: status output** — Run `/status` with a Now item that has backlog + spec but no plan; verify Pipeline Detail line shows `spec ✓ plan —`.

## Acceptance Criteria

- [ ] `/status` shows a Problem excerpt per Now/Ready item (max 120 chars)
- [ ] Spec and plan existence shown as ✓/— per item
- [ ] Section omitted when Now and Ready are both empty
- [ ] No changes to `utils_roadmap.py` or ROADMAP format
- [ ] All tests pass