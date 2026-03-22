---
description: Turn a backlog item into a written spec with Acceptance Criteria. Second stage of the SDLC pipeline.
argument-hint: "[slug] — backlog item slug (e.g. zie-spec add-csv-export)"
allowed-tools: Read, Write, Glob, Skill
---

# /zie-spec — Backlog → Spec

Write a design spec for a backlog item. Invokes spec-design skill with
reviewer loop. Output lives in `zie-framework/specs/`.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → zie_memory_enabled.

## Steps

1. If slug provided → read `zie-framework/backlog/<slug>.md`.
   If not → read ROADMAP.md Next section, list items, ask: "Which to
   spec? Enter number."
2. Invoke `Skill(zie-framework:spec-design)` with backlog content as context:
   - Skill asks clarifying questions, proposes approaches, presents
     design, writes spec, runs spec-reviewer loop until approved.
   - Spec saved to `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`.
3. Print:

   ```text
   Spec written: zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: /zie-plan <slug> to create the implementation plan.
   ```

## ขั้นตอนถัดไป

→ `/zie-plan <slug>` — เมื่อ spec approved แล้ว
→ `/zie-status` — ดูภาพรวม

## Notes

- Always spec-first — never skips to plan without an approved spec
- Spec-reviewer loop runs automatically inside spec-design skill
