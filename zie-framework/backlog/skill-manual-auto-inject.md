---
tags: [feature]
---

# Auto-inject SKILL.md Rules into Sessions

## Problem

SKILL.md contains framework rules (data sources, anti-patterns, workflow) but is never automatically injected into Claude's context. The rules are hardcoded in `session-resume.py` instead, which means:
- Adding a new rule requires editing both SKILL.md AND session-resume.py
- After context compaction, rules are lost (only active task survives)
- Claude doesn't know that ROADMAP.md is the source of truth for backlog queries

## Motivation

When a user asks "what's in the backlog?", Claude scans directories because no rule tells it to read ROADMAP.md instead. Making SKILL.md the source of truth and having hooks read from it means one edit updates everything.

## Rough Scope

**In:**
- Modify `session-resume.py`: read SKILL.md "Data Sources" + "Key Rules" sections, inject as `additionalContext` at session start
- Modify `sdlc-compact.py`: include Data Sources rule in post-compact context (survives context window compression)
- Remove hardcoded workflow + anti-patterns strings from `session-resume.py` — read from SKILL.md instead
- Keep dynamic command scan (`zie_context_loader.py`) unchanged — it already works correctly

**Out:**
- Changing `intent-sdlc.py` (no need — it handles intent nudges, not rules)
- Changing `zie_context_loader.py` (no need — it handles command scanning, not rules)
- Making SKILL.md user-invocable (stays `false` — injected automatically instead)