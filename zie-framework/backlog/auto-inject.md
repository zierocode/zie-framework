---
tags: [feature]
---

# Auto-Inject — context พร้อมเมื่อ session เริ่ม

## Problem

User ต้อง run `/load-context` หรือ `/status` เองเพื่อโหลด context. Session ใหม่เริ่ม fresh ทุกครั้ง.

## Motivation

Auto-load context at session start. Load previous session memory, relevant context (keyword search), present summary. User just "continue".

## Rough Scope

**In:**
- `hooks/session-resume.py` — auto-inject context
- Load session memory from previous session
- Keyword-based context retrieval
- Present summary + "Continue?" prompt

**Out:**
- Manual /load-context (still available but not needed)

<!-- priority: HIGH -->
<!-- depends_on: unified-context-cache -->
