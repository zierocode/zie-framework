# Backlog: Sync PROJECT.md commands + skills table (hub is 23% inaccurate)

**Problem:**
PROJECT.md (the knowledge hub) has two accuracy gaps:
1. Commands table: missing /sprint, /chore, /hotfix, /spike (4 of 15 commands)
2. Skills table: retro-format listed but deleted (sprint8); load-context and
   reviewer-context not listed (added sprint8, ADR-048)

CLAUDE.md has the same gap in its SDLC Commands table (also missing the 4 commands).
docs-sync-check never validates PROJECT.md so this drift is invisible to automation.

**Motivation:**
A user reading PROJECT.md has no idea /sprint, /hotfix, /spike, or /chore exist.
A developer reading the Skills table sees a ghost (retro-format) and misses two
active skills. This is the primary onboarding document — 23% inaccuracy undermines
trust and discoverability.

**Rough scope:**
- Add /sprint, /chore, /hotfix, /spike to PROJECT.md Commands table
- Add /sprint, /chore, /hotfix, /spike to CLAUDE.md SDLC Commands table
- Remove retro-format from PROJECT.md Skills table
- Add load-context and reviewer-context to PROJECT.md Skills table
- Tests: docs-sync-check extended scope (see separate backlog item)
