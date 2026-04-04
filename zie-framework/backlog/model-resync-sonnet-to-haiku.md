# Backlog: Downgrade /resync model sonnet → haiku (scan + write, no judgment needed)

**Problem:**
/resync uses `model: sonnet` + `effort: medium`. resync scans the codebase via an
Explore agent, then updates PROJECT.md and knowledge docs with what was found.
The main thread is mechanical: receive Explore output → write structured docs.
The heavy lifting (codebase understanding) is done by the Explore subagent, not
the main resync command.

**Motivation:**
sonnet is overkill for a doc-update coordinator. haiku+medium can read Explore
output and update structured markdown docs correctly. Downgrading saves model
cost on every /resync run.

**Rough scope:**
- Change `model: sonnet` → `model: haiku` in commands/resync.md frontmatter
- Keep `effort: medium` (haiku benefits from it here since output needs structure)
  OR drop to `effort: low` if haiku handles it correctly in testing
- Tests: resync correctly updates PROJECT.md components table after model change
