---
description: Project audit across 9 dimensions — security, efficiency, quality, docs, architecture, observability, deps, performance, external research. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: sonnet
effort: medium
---

# /audit — Project Audit

<!-- preflight: full -->

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).

Parse `--focus <dim>` from `$ARGUMENTS` if present (e.g. `--focus security`).

Invoke `Skill(zie-framework:audit)` passing `--focus <dim>` or no args.

Phases: [Phase 1/3] dimension research (Agent ✓), [Phase 2/3] synthesis, [Phase 3/3] backlog. [Research 1/15] per WebSearch.

→ /backlog to capture audit findings
