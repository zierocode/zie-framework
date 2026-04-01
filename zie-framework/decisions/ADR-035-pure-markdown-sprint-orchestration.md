# ADR-035 — Pure Markdown Sprint Orchestration

**Status:** Accepted
**Date:** 2026-04-01

## Context
/zie-sprint needs to orchestrate complex multi-phase execution across multiple features. Two implementation approaches were considered: (1) a new Python orchestrator hook, or (2) a Markdown command using existing Agent+Skill tools.

## Decision
Implement /zie-sprint as a Markdown command (commands/zie-sprint.md) that delegates to Agent() and Skill() tools for each phase. Zero new Python hooks. The command is pure orchestration prose.

## Consequences
**Positive:** No new runtime dependencies. Command is readable and maintainable. Uses battle-tested Agent/Skill tools. Safe to modify without risk of breaking hook infrastructure.
**Negative:** Cannot execute shell commands directly — must delegate to subagents.
**Neutral:** Consistent with how all other /zie-* commands work.

## Alternatives
- Python orchestrator: faster but adds Python complexity to hook layer
- Shell script: simpler but harder to integrate with Claude tools
