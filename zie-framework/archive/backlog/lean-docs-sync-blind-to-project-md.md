# Backlog: Extend docs-sync-check to verify PROJECT.md

**Problem:**
docs-sync-check only verifies CLAUDE.md and README.md against commands/*.md and
skills/*/SKILL.md filenames. PROJECT.md (the knowledge hub) is never enumerated
or compared. Since PROJECT.md is the main user-facing reference, stale entries
there (deleted skills, missing commands) are never caught by the automated check.

**Motivation:**
The structural audit found 23% inaccuracy in PROJECT.md's commands/skills tables —
a ghost entry + 2 missing skills + 4 missing commands. None of this was flagged by
docs-sync-check. The tool's blind spot is exactly the most important doc in the repo.

**Rough scope:**
- Add PROJECT.md to the docs-sync-check skill's verification scope
- Check: every command basename in commands/*.md has a row in PROJECT.md Commands table
- Check: every skill dirname in skills/*/ has a row in PROJECT.md Skills table
- Check: no row in PROJECT.md references a non-existent command/skill file
- Emit STALE verdict for PROJECT.md when gaps found
- Tests: unit test with synthetic PROJECT.md missing a command row
