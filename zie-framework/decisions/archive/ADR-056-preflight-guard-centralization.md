# ADR-056 — Pre-flight Guard Centralization

**Status**: Accepted
**Date**: 2026-04-04

## Context

Six commands (spec, plan, fix, backlog, resync, implement) each duplicated the same 3-step pre-flight guard inline: check `zie-framework/` exists, read `.config`, check ROADMAP Now lane. Any change to guard semantics required 6 separate edits and 6 failing tests.

## Decision

Extract the canonical 3-step pre-flight protocol to `zie-framework/project/command-conventions.md` and replace all inline copies with a single reference line: `See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight)`.

## Consequences

**Positive:**
- Future commands get the guard for free by referencing the document
- Guard semantic changes require one file edit + one test update, not 6
- `test_command_conventions.py` (4 tests) provides a single regression harness

**Negative:**
- Commands now depend on an external file — broken link would silently remove guard context
- Slightly less self-contained command files

**Neutral:**
- Commands with special guard variants (implement: ROADMAP required, spec/plan: Now-lane check) retain inline notes after the reference line

## Alternatives

- **Keep duplicated inline guards**: Simpler per-file, but maintenance burden scales with number of commands
- **Generate guards at build time**: Overkill for a prompt file; no build step exists
