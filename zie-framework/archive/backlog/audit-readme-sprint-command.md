# /zie-sprint missing from README.md commands table

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

`/zie-sprint` was added in v1.15.0 and is documented in CLAUDE.md and
`zie-framework/PROJECT.md`, but it is entirely absent from the README.md
Commands table — the primary public-facing documentation for plugin consumers.

A developer discovering the plugin via README would have no visibility into
the sprint-clear batch pipeline command.

## Motivation

Add `/zie-sprint` row to the Commands table in README.md with a one-line
description matching CLAUDE.md. Also verify the docs-sync-check skill catches
this class of gap in future.
