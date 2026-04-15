---
tags: [feature]
---

# ROADMAP Now Singleton Injection

## Problem

The same ROADMAP "Now" content is parsed and injected into context by 5+ hooks independently:
- session-resume.py (SessionStart)
- intent-sdlc.py (UserPromptSubmit)
- subagent-context.py (SubagentStart)
- failure-context.py (PostToolUseFailure)
- sdlc-compact.py (PreCompact/PostCompact)

Each independently calls `parse_roadmap_section_content()` with the same result. The "Active: {feature} | stage: {stage}" string appears 2-5 times per session, wasting 200-500 tokens.

## Motivation

ROADMAP Now rarely changes during a session. Parsing and injecting it once, then referencing the cached result, would eliminate redundant parsing and reduce context duplication.

## Rough Scope

**In:**
- Create a session-scoped "Now item" singleton: first hook to read ROADMAP Now writes it to a cache file (e.g., `.zie/cache/now-item.json`)
- Subsequent hooks read from cache instead of parsing ROADMAP again
- Invalidate cache on Write/Edit to ROADMAP.md (via PostToolUse hook)
- Each hook outputs its own formatted context but reads Now data from cache

**Out:**
- Changing hook output format
- Changing ROADMAP format
- Removing Now item from any hook output entirely (each hook should still output its own context line)