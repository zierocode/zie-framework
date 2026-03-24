---
description: Turn a backlog item into a written spec with Acceptance Criteria. Second stage of the SDLC pipeline.
argument-hint: "[slug|\"idea\"] — backlog slug or inline idea string (e.g. zie-spec add-csv-export OR zie-spec \"add rate limiting\")"
allowed-tools: Read, Write, Edit, Glob, Skill
---

# /zie-spec — Backlog → Spec

Write a design spec for a backlog item. Invokes spec-design skill with
reviewer loop. Output lives in `zie-framework/specs/`.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project_type, zie_memory_enabled.
3. Read `zie-framework/ROADMAP.md` → check Now lane.
   - If a `[ ]` item exists → warn: "WIP active: `<feature>`. Specs can be
     written in parallel but focus is split. Continue? (yes/no)"
   - If no → stop.

## Steps

1. **Detect input mode:**

   - If arg is provided:
     - Check `zie-framework/backlog/<arg>.md` exists → **slug mode**: read
       backlog file → continue to step 2.
     - Arg contains spaces → **quick mode**: go to quick-spec flow (step 3).
     - No backlog file + single word → **quick mode** + warn: "No backlog
       file found for '`<arg>`' — treating as inline idea."
   - If no arg → read ROADMAP.md Next section, list items, ask: "Which to
     spec? Enter number." → slug mode.

2. **Slug mode** (existing flow): pass backlog file content to
   `Skill(zie-framework:spec-design)` with `zie_memory_enabled` from
   .config. Skill calls `mcp__plugin_zie-memory_zie-memory__recall` for context when brain is enabled.
   Spec saved to `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`
   with `approved: true` in frontmatter once reviewed.

   Commit spec after approval:

   ```bash
   git add zie-framework/specs/YYYY-MM-DD-<slug>-design.md
   git commit -m "spec: <slug>"
   ```

   Go to step 4.

3. **Quick spec mode** (new): print "Quick spec mode — skipping backlog.
   Starting spec design..."

   - Derive slug: kebab-case of first 5 words of idea string.
     Example: `"add rate limiting to API"` → `add-rate-limiting-to-api`
   - Check slug collision: if `zie-framework/specs/*-<slug>-design.md`
     already exists → append `-2`, `-3`, etc.
   - Pass idea string directly to `Skill(zie-framework:spec-design)` as
     context (idea string becomes the problem statement — no backlog file
     needed).
   - spec-design asks clarifying questions, proposes approaches, writes
     spec, runs spec-reviewer loop, records `approved: true` in frontmatter.
   - After spec approved, add to ROADMAP Next:
     `- [ ] <idea title> — [spec](specs/YYYY-MM-DD-<slug>-design.md)`

   Commit spec + ROADMAP after approval:

   ```bash
   git add zie-framework/specs/YYYY-MM-DD-<slug>-design.md \
     zie-framework/ROADMAP.md
   git commit -m "spec: <slug>"
   ```

4. Print handoff (both modes):

   ```text
   Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: /zie-plan <slug> to create the implementation plan.
   ```

## ขั้นตอนถัดไป

→ `/zie-plan <slug>` — เมื่อ spec approved แล้ว
→ `/zie-retro` — ถ้า spec session ยาวและมี learnings ที่ควรบันทึก
→ `/zie-status` — ดูภาพรวม

## Notes

- Always spec-first — never skips to plan without an approved spec
- Quick mode: `/zie-spec "idea"` skips backlog file, goes straight to spec-design
- Quick mode adds item to ROADMAP Next with spec link (no backlog file created)
- spec-design writes `approved: true` frontmatter after reviewer passes
- /zie-plan checks this frontmatter — draft specs do not proceed to plan
- spec-design does NOT auto-invoke write-plan (commands are control plane)
