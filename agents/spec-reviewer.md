---
description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
isolation: worktree
allowed-tools: Read, Glob, Grep
---

# spec-reviewer agent

Invoke `Skill(zie-framework:spec-reviewer)` with the spec path and backlog context
provided by the caller.
