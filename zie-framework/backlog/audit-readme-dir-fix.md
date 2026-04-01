# Doubled path component in README.md directory structure

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

README.md directory structure section lists `project/context.md` under a path
that resolves to `zie-framework/project/project/context.md` — the `project/`
component is doubled. The actual path on disk is `zie-framework/project/`.

## Motivation

One-line fix in README.md. Correct path representation prevents contributor
confusion when navigating the project structure.
