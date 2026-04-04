# Backlog: Drop /retro effort medium → low (structured write, not creative)

**Problem:**
/retro uses `model: sonnet` + `effort: medium`. retro is structured writing:
read git log, write ADR entries from template, update ROADMAP Done section,
run docs-sync-check. None of these steps require extended reasoning — they follow
a fixed template with slot-filling from git history.

**Motivation:**
medium effort on sonnet costs noticeably more than low. The output quality of ADR
writing and ROADMAP updates is not meaningfully improved by extended thinking —
it's template-driven structured output that sonnet handles well at low effort.

**Rough scope:**
- Change `effort: medium` → `effort: low` in commands/retro.md frontmatter
- Tests: retro produces valid ADR format + ROADMAP entry at low effort
