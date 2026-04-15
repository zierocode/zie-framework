# ADR-051 — Command Namespace Flattening (Remove zie- Prefix)

**Status:** Accepted
**Date:** 2026-04-04

## Context

All 15 commands lived in `commands/zie-*.md` and were invoked as `/zie-backlog`,
`/zie-implement`, etc. The `zie-` prefix was redundant since commands are already
namespaced under the `zie-framework` plugin. The prefix increased friction for CLI
flows and made command names harder to type.

## Decision

Renamed all `commands/zie-*.md` → `commands/*.md` (e.g., `zie-backlog.md` →
`backlog.md`). Invocation becomes `zie-framework:backlog` instead of
`zie-framework:zie-backlog`. Skill directory names (`skills/audit/`,
`skills/zie-memory/`, etc.) were intentionally NOT renamed — skill invocations use
internal paths that are not user-typed, and renaming would break existing plugin
marketplace references.

## Consequences

**Positive:**
- Cleaner invocation surface for CLI workflows
- Command filenames match their semantic purpose (`backlog.md` vs `zie-backlog.md`)
- Reduces character count for command typing

**Negative:**
- Breaking change: any external references to `zie-framework:zie-backlog` are now broken
- Required 700+ cross-file updates across tests, hooks, skills, agents, docs
- Asymmetric naming: commands are flattened but skills still have zie- prefix

**Neutral:**
- 46 test files updated; integration tests also required separate pass
- Three-pass sed strategy (path refs → content assertions → quoted literals) established
  as a reusable rename pattern

## Alternatives Considered

- **Rename both commands and skills**: Higher blast radius; skills have external callers
- **Keep zie- prefix**: Status quo; no change in ergonomics
- **Alias both**: Complex; two code paths to maintain
