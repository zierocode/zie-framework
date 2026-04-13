---
tags: [feature]
---

# Full Framework Compatibility Audit with GLM-5.1:Cloud

## Problem

Parts of zie-framework rely on Claude Code-specific features (model: frontmatter, --agent flag, Skill() tool, MCP tools, specific tool names) that may silently break or degrade under `glm-5.1:cloud`. The existing `agent-mode-compat` backlog item covers agent-mode + model frontmatter, but a broader audit is needed to verify end-to-end compatibility across all hooks, commands, skills, tests, and Makefile targets.

## Motivation

Zie is actively using `glm-5.1:cloud` as the current session model. Without a full compatibility check, unknown breakage may lurk in hooks (Claude-specific tool assumptions), skills (Skill() tool availability), commands (tool name differences), and tests (model-specific assertions). Knowing the exact compatibility gap — and whether it's 100% or not — lets us fix issues proactively rather than discovering them mid-pipeline.

## Rough Scope

- **In**: Audit every hook, command, skill, and test for Claude-specific assumptions (tool names, model tiers, --agent, Skill() availability, MCP tool availability). Identify hard breaks vs graceful degradation. Produce a compatibility matrix.
- **In**: Cross-reference with existing work: ADR-066 (GLM/Ollama compatibility), `agent-mode-compat` backlog item, `release-non-claude-fallback` (v1.28.1).
- **Out**: Implementing fixes (that's a separate spec/plan). This item is audit-only.
- **Related**: `agent-mode-compat` (subset — agent mode + model frontmatter), ADR-066 (existing GLM/Ollama detection).