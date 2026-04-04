# Align load-context ADR Cache Protocol

## Problem

`skills/load-context/SKILL.md` always reads all `decisions/*.md` from disk unconditionally before calling `write_adr_cache`. In contrast, `skills/reviewer-context/SKILL.md` calls `get_cached_adrs` first and only falls back to disk on cache miss. The two ADR-loading skills have divergent protocols.

## Motivation

In a single `/implement` session with multiple impl-reviewer invocations, the ADR corpus (currently 26 files) is read N+1 times instead of once. Adding a `get_cached_adrs` cache-check as step 0 in `load-context` makes it match `reviewer-context` and cuts redundant disk reads per session.

## Rough Scope

- In: prepend cache-check step to `load-context` SKILL.md; skip raw read loop on cache hit + mtime match
- Out: no changes to `reviewer-context` or reviewer skills
