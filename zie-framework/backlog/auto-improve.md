---
tags: [feature]
---

# Auto-Improve — high-confidence patterns ถูก apply อัตโนมัติ

## Problem

Patterns ที่ extract ได้ต้อง apply ด้วยมือ. ไม่มี auto-apply.

## Motivation

Auto-apply high-confidence patterns (>0.95). Update MEMORY.md automatically, propose ADR if significant, suggest config changes.

## Rough Scope

**In:**
- `commands/retro.md` — auto-mode
- Pattern aggregation + ranking
- Auto-apply threshold (0.95)
- ADR generation for significant patterns

**Out:**
- Low-confidence patterns (require manual review)

<!-- priority: MEDIUM -->
<!-- depends_on: auto-learn -->
