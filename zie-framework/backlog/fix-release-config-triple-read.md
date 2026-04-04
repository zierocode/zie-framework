# Fix Release Config Triple Read

## Problem

`/release` reads `zie-framework/.config` three times in a single run: once at pre-flight (line 13), then twice more inline during Gate 3 and Gate 4 to check `playwright_enabled` and `has_frontend`. The values are already in scope from the pre-flight read.

## Motivation

Redundant reads add cognitive overhead for maintainers tracing the flow, and waste context tokens loading the same ~20-line JSON file multiple times. Binding at pre-flight and referencing by variable is a clearer pattern.

## Rough Scope

- In: bind `config` at pre-flight; reference `config.playwright_enabled` and `config.has_frontend` in Gates 3+4
- Out: no behavior change, no other commands
