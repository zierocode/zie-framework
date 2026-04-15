---
tags: [feature]
---

# Auto-Learn — patterns ถูก extract เมื่อ session จบ

## Problem

User ต้อง run `/retro` เองเพื่อ extract patterns. Session จบ = ความรู้หาย.

## Motivation

Auto-extract patterns at session end. Save to session memory, present suggestions. High-confidence patterns auto-applied.

## Rough Scope

**In:**
- `hooks/session-stop.py` — auto-capture + pattern extraction
- Session memory format (JSON schema)
- High-confidence pattern detection (threshold 0.95)
- Write `.zie/memory/session-[timestamp].json`

**Out:**
- Manual /retro (still available for deep review)

<!-- priority: HIGH -->
<!-- depends_on: auto-inject -->
