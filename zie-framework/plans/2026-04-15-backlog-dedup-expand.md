---
date: 2026-04-15
status: approved
slug: backlog-dedup-expand
---

# Backlog Dedup and Expand — Implementation Plan

## Steps

1. **Update `commands/backlog.md` step 3d** — after step 3c token-overlap check, add a scan of Ready and Done ROADMAP sections. Use `parse_roadmap_section_content(roadmap_path, "ready")` and `parse_roadmap_section_content(roadmap_path, "done")` to collect item titles. Tokenize each title the same way as step 3c. If ≥2 tokens overlap, warn: `"Similar item exists in <section>: <title>"`. Print all warnings before continuing.

2. **Update `commands/backlog.md` step 3e** — after warnings, check if any overlap score equals the full token set (all tokens match → likely duplicate). If found, ask: `"Duplicate detected: backlog/<slug>.md. Expand existing item? (y/n)"`. If yes, append `## Additional Scope\n\n<new context from user>` to the existing file and stop (skip steps 4-7). If no, continue as normal.

3. **Update step 3c** — currently only scans `zie-framework/backlog/` filenames. Enhance to also extract the `# Title` line from each `.md` file and include those tokens in the overlap comparison. This catches items where slug differs but title matches.

4. **Verify no Python hook needed** — all logic lives in the skill prompt (`commands/backlog.md`), which Claude executes. No new Python files required.

## Tests

- `test_backlog_dedup_next_overlap()` — step 3c catches a Next-lane item with overlapping slug tokens
- `test_backlog_dedup_ready_overlap()` — step 3d catches a Ready-lane item with overlapping title tokens
- `test_backlog_dedup_done_overlap()` — step 3d catches a Done-lane item with overlapping title tokens
- `test_backlog_dedup_expand()` — step 3e expands existing item with `## Additional Scope` instead of creating new file
- `test_backlog_dedup_no_match()` — no overlap found, normal creation proceeds

Tests are manual skill-test validations (check that `/backlog` command text includes the new steps), not unit tests for Python hooks.

## Acceptance Criteria

- [ ] `/backlog` warns about similar items in Next, Ready, and Done lanes
- [ ] Full-token-match duplicates offer expand instead of create
- [ ] Expanding appends `## Additional Scope` and skips new-file creation
- [ ] Step 3c enhanced to check title text, not just slug filenames
- [ ] No-match case proceeds unchanged