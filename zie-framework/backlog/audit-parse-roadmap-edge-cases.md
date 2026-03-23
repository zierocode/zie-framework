# parse_roadmap_now() untested for nested markdown and malformed links

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`test_utils.py:35-39` doesn't cover: markdown nesting inside task lines
(`**bold**`, `_italic_`), malformed link syntax `[title](url` (missing closing
paren), or HTML entities in task descriptions. These are realistic ROADMAP
content patterns.

## Motivation

parse_roadmap_now is called on every SessionStart and wip-checkpoint. A parsing
edge case that silently drops tasks would cause session context to be incomplete,
leading Claude to miss active work items.
