---
tags: [chore]
---

# Revise SKILL.md Files — Compress for Token Efficiency

## Problem

`SKILL.md` files for skills like spec-design, write-plan, and debug contain verbose instructional text that can be compressed by 20-30% without losing functionality. This adds unnecessary token cost to every skill invocation.

## Rough Scope

**In:**
- Revise and compress all `SKILL.md` files — remove redundant explanations, use tables for structured data
- Extract long prompts to `templates/` where appropriate
- Target 20% reduction across all skill files
- Verify each skill still works correctly after compression (functional parity)

**Out:**
- Changing skill behavior or workflow steps
- Removing essential instructions that affect correctness

## Priority

MEDIUM