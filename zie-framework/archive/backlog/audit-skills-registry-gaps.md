# 10 skills not listed in PROJECT.md components section

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

PROJECT.md is the navigation hub for the project. The components section
references commands and hooks but omits the 10 skills in `skills/`. Users and
contributors reading PROJECT.md cannot discover what skills exist without
manually globbing the filesystem.

## Motivation

Skills are the primary quality gate mechanism (spec-reviewer, plan-reviewer,
impl-reviewer, etc.). They should be first-class documented components, not
implicit filesystem knowledge.
