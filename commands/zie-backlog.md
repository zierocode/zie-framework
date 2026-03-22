---
description: Capture a new backlog item — problem, motivation, rough scope. First stage of the SDLC pipeline.
argument-hint: Optional idea title (e.g. "add CSV export")
allowed-tools: Read, Write, Glob
---

# /zie-backlog — Capture Backlog Item

Capture a new idea as a backlog item. No spec or plan yet — just the
problem and motivation. Output lives in `zie-framework/backlog/`.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → zie_memory_enabled.
3. If `zie_memory_enabled=true`:
   - `recall project=<project> domain=<domain> tags=[backlog] limit=10`
   - Check for duplicates — warn if similar item already exists.

## Steps

1. If argument provided → use as idea title. If not → ask: "What's the
   idea? (one line title)"
2. Derive slug: lowercase, replace spaces with hyphens, strip punctuation.
3. Write `zie-framework/backlog/<slug>.md`:

   ```markdown
   # <Idea Title>

   ## Problem

   <what problem does this solve — 1-3 sentences>

   ## Motivation

   <why this matters now — who benefits and how>

   ## Rough Scope

   <optional — what's in and out>
   ```

4. Update `zie-framework/ROADMAP.md` Next section:
   `- [ ] <title> — [backlog](backlog/<slug>.md)`

5. If `zie_memory_enabled=true`:
   - `remember "Backlog: <title>. Problem: <one-line>." tags=[backlog, <project>]`

6. Print:

   ```text
   Backlog item added: zie-framework/backlog/<slug>.md
   ROADMAP updated → Next

   Next: /zie-spec <slug> to write the spec.
   ```

## ขั้นตอนถัดไป

→ `/zie-spec <slug>` — เมื่อพร้อมเขียน spec
→ `/zie-status` — ดูภาพรวม backlog

## Notes

- Can be run with argument: `/zie-backlog "add CSV export"` to skip prompt
- Safe to re-run — will warn if slug already exists
