# PROJECT.md version stale: shows 1.4.0, current is 1.4.1

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`zie-framework/PROJECT.md:7` shows `**Version**: 1.4.0` but the current version
is 1.4.1 per `plugin.json` and `VERSION` file. The project hub document is the
first thing read on every session — an incorrect version creates confusion.

## Motivation

Trivial fix (XS effort). The release process should include updating PROJECT.md
version, or the `sync-version` Makefile target should cover it.
