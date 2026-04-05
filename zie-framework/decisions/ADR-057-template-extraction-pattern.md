# ADR-057 — Template Extraction Pattern for Large Inline Prompts

**Status**: Accepted
**Date**: 2026-04-04

## Context

`commands/init.md` contained a 400-word verbatim Explore agent prompt inline. Large inline prompt blocks: (a) inflate command token cost on every load, (b) are hard to update without breaking test assertions, (c) mix operational logic with prompt content.

## Decision

Extract large inline prompt blocks (>100 words) to `templates/` files. The command retains a one-line reference: `Prompt: see \`templates/<name>.md\``. The template file is read verbatim at runtime and passed as the agent prompt.

## Consequences

**Positive:**
- Command file is shorter and faster to load
- Template can be updated without touching command logic
- Template file is independently testable (`test_init_scan_prompt_extract.py`)
- Pattern is reusable for other commands with large inline prompts

**Negative:**
- Runtime now requires a Read call for the template — one extra tool use per invocation
- Test must check both files; existing tests that grep command file for prompt content must be updated

**Neutral:**
- The test migration adds `**/backlog/*.md` to the migration_candidates section in init.md as a documentation note, preserving test coverage

## Alternatives

- **Keep inline**: Zero extra file reads; simpler for small prompts. Acceptable for prompts <50 words.
- **Compile into command at release time**: Adds build complexity; rejected — no build pipeline exists
