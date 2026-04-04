---
description: Capture a new backlog item — problem, motivation, rough scope. First stage of the SDLC pipeline.
argument-hint: Optional idea title (e.g. "add CSV export")
allowed-tools: Read, Write, Glob
model: haiku
effort: low
---

# /backlog — Capture Backlog Item

Capture a new idea as a backlog item. No spec or plan yet — just the
problem and motivation. Output lives in `zie-framework/backlog/`.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).

2. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__recall`
     with `project=<project> domain=<domain> tags=[backlog, <project>] limit=10`
   - Check for duplicates — warn if similar item already exists.

## Steps

1. If argument provided → use as idea title. If not → ask: "What's the
   idea? (one line title)"
2. Derive slug using: `re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')`
   Example: "Add CSV Export!" → `add-csv-export`
3. **Re-run guard**: if `zie-framework/backlog/SLUG.md` already exists →
   print "Backlog item 'SLUG' already exists. Edit the file directly or
   use a different title." and stop.

3b. **Infer tag** from title using keyword map (case-insensitive, first match wins):
    - `bug`: fix, error, crash, broken
    - `chore`: cleanup, update, bump, refactor
    - `debt`: tech debt, debt, legacy, slow
    - `feature`: add, new, implement, support (default)

    Capture inferred tag as `<inferred-tag>`.

3c. **Duplicate check**: split new slug by `-` → token set. For each `.md` file in
    `zie-framework/backlog/`:
    - Tokenize its basename (strip `.md`, split by `-`)
    - If ≥2 tokens overlap with new slug → warn: `"Similar item exists: backlog/<slug>.md"`
    - Does NOT block creation. Print all warnings before continuing.

4. Write `zie-framework/backlog/<slug>.md`:

   ```markdown
   ---
   tags: [<inferred-tag>]
   ---

   # <Idea Title>

   ## Problem

   <what problem does this solve — 1-3 sentences>

   ## Motivation

   <why this matters now — who benefits and how>

   ## Rough Scope

   <optional — what's in and out>
   ```

5. Update `zie-framework/ROADMAP.md` Next section:
   `- [ ] <title> — [backlog](backlog/<slug>.md)`

6. **Commit backlog item**:

   ```bash
   git add zie-framework/backlog/<slug>.md zie-framework/ROADMAP.md
   git commit -m "backlog: <slug>"
   ```

7. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Backlog: <title>. Problem: <one-line>." tags=[backlog, <project>]`

8. Print:

   ```text
   Backlog item added: zie-framework/backlog/<slug>.md
   ROADMAP updated → Next

   Next: /spec <slug> to write the spec.
   ```

## ขั้นตอนถัดไป

→ `/spec <slug>`

