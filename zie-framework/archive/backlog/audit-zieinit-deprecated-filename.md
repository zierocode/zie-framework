# zie-init.md shows deprecated `project/decisions.md` filename

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`commands/zie-init.md:215,219` still references `project/decisions.md` in code
examples. This file was renamed to `project/context.md` in v1.3.0. New projects
initialized with `/zie-init` will generate the wrong filename reference in their
documentation examples.

## Motivation

zie-init is the entry point for all new projects using this framework. A stale
filename in the template propagates the error to every downstream project.
