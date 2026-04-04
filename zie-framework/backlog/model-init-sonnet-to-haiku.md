# Backlog: Downgrade /init model sonnet → haiku (scaffold setup, Explore does the work)

**Problem:**
/init uses `model: sonnet` + `effort: medium`. init bootstraps a project: creates
directory structure, copies templates, writes initial ROADMAP/PROJECT.md stubs.
The discovery step uses an Explore subagent. The main thread creates files from
templates — mechanical work that doesn't require sonnet-level reasoning.

**Motivation:**
sonnet is overkill for file scaffolding and template copying. haiku+medium handles
structured file creation correctly. Saves model cost on every new project init.

**Rough scope:**
- Change `model: sonnet` → `model: haiku` in commands/init.md frontmatter
- Tests: init correctly creates all expected directories and files after model change
