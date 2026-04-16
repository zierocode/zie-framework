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

Parse `--focus <dim>` from `$ARGUMENTS` if present. Invoke `Skill(zie-framework:audit)`.

→ /backlog to capture findings
