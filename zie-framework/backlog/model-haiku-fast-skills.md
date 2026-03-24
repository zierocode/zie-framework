# Backlog: model:haiku + effort:low for Fast/Status Skills

**Problem:**
Every zie-framework skill uses Claude's default model (currently Sonnet).
/zie-status, which just reads files and formats output, runs on the same model
as /zie-spec which needs deep design thinking. This wastes cost and latency.

**Motivation:**
Skills support `model:` and `effort:` frontmatter fields. Routing fast,
structured tasks (status checks, simple lookups, session-resume summaries) to
haiku (3x faster, 5x cheaper) with `effort: low` improves responsiveness
without sacrificing quality for tasks that don't need it.

**Rough scope:**
- `model: haiku` + `effort: low` on: zie-status, session-resume context
  (SessionStart additionalContext), simple query skills
- `effort: high` on: zie-spec, zie-plan (complex design tasks benefit from
  extended thinking)
- `effort: medium` (default) on: zie-implement, zie-fix (balanced)
- `model: inherit` on: reviewers-as-agents (already set to haiku there)
- Document model/effort choices in each skill's frontmatter with a comment
- Tests: frontmatter fields parse without error, no skill regression
