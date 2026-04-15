---
tags: [feature]
---

# Auto-Decide — เสนอ action ที่เหมาะสมระหว่างทาง

## Problem

Claude รอ user บอกให้ทำอะไรทุกขั้น. ไม่มีการเสนอ action อัตโนมัติ.

## Motivation

Auto-suggest next actions during session. Detect patterns, suggest fixes, propose next steps. Never force, always offer "skip".

## Rough Scope

**In:**
- `hooks/post-tool-use.py` — active suggestions
- Pattern-based recommendations
- "Continue?" prompts after key events
- Test failure detection → suggest /fix

**Out:**
- User control (always can skip)

<!-- priority: MEDIUM -->
<!-- depends_on: auto-learn -->
