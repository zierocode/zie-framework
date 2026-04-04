---
description: Project audit across 9 dimensions — security, efficiency, quality, docs, architecture, observability, deps, performance, external research. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: sonnet
effort: medium
---

# /audit — Project Audit

Parse `--focus <dim>` from `$ARGUMENTS` if present (e.g. `--focus security`).

Invoke `Skill(zie-framework:zie-audit)` passing `--focus <dim>` or no args.

The skill handles all audit phases, agent dispatch, synthesis, scoring, and backlog selection.
