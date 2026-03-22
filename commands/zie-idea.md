---
description: Turn an idea into a written spec and actionable implementation plan. Runs brainstorming and writing-plans in sequence.
argument-hint: Optional idea description (e.g. "add CSV export for memories")
allowed-tools: Read, Write, Bash, Glob, Grep, Skill, TaskCreate
---

# /zie-idea — Brainstorm → Spec → Implementation Plan

Turn an idea into a written spec and actionable implementation plan. Runs brainstorming and writing-plans in sequence. Output lives in `zie-framework/specs/` and `zie-framework/plans/`.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` for project context.
3. If `zie_memory_enabled=true` — READ (1 batch query):
   - `recall project=<project> domain=<domain> limit=15`
   - Returns: past backlog items, shipped features, retro patterns in one call.
   - Use to: detect duplicates, surface prior approaches. Cache result — do not re-query within this session.

## Steps

### สร้าง spec

1. Invoke `Skill(zie-framework:spec-design)` with the user's idea as context:
   - Skill asks clarifying questions, proposes approaches, presents design sections, writes spec.
   - Spec saved to `zie-framework/specs/YYYY-MM-DD-<topic>-design.md`.
   - Do NOT auto-commit. Only commit when Zie explicitly requests it.

2. Ask user: "Spec looks good? Proceed to implementation plan?"
   - If no → revise and re-ask.

### เขียน implementation plan

1. Invoke `Skill(zie-framework:write-plan)` with the approved spec:
   - Skill writes a task-by-task TDD plan.
   - Plan saved to `zie-framework/plans/YYYY-MM-DD-<topic>.md`.

### อัปเดต ROADMAP และ backlog

1. Update `zie-framework/ROADMAP.md`:
   - Add feature to "Next" section only: `- [ ] <feature name> — [idea](backlog/<slug>.md)`
   - Create `zie-framework/backlog/<slug>.md` with 1-2 paragraph description of the idea.
   - Do NOT move to Now or Ready. Feature stays in backlog until /zie-plan is run.

1b. If `zie_memory_enabled=true` — WRITE:

- `remember "Backlog item added: <slug>. Problem: <one-line summary>. Domain: <domain>." tags=[backlog, <project>, <domain>]`

1. Print:

   ```text
   Backlog item  → zie-framework/backlog/<slug>.md
   ROADMAP updated → Next (backlog)

   Run /zie-plan <slug> when ready to create an implementation plan.
   ```

## ขั้นตอนถัดไป

→ `/zie-plan <slug>` — เมื่อพร้อม draft implementation plan
→ `/zie-status` — ดูภาพรวม backlog

## Notes

- Can be run with argument: `/zie-idea "export memories as CSV"` to skip the initial prompt
- Can be run without argument: will ask for the idea first
- Always spec-first — never skips to plan without an approved spec
