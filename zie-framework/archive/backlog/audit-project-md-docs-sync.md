# docs-sync-check skill missing from PROJECT.md skills table

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

`docs-sync-check` exists on disk at `skills/docs-sync-check/SKILL.md` and is
listed in README.md, but is absent from `zie-framework/PROJECT.md` skills
table. PROJECT.md is the internal knowledge hub — missing skills there means
the codebase map is stale.

## Motivation

Add `docs-sync-check` row to PROJECT.md skills table. Verify the
docs-sync-check skill itself catches this class of gap going forward (it
should be flagging its own absence).
