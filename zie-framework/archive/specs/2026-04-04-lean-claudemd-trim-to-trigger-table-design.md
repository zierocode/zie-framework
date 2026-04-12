# Lean CLAUDE.md — Trim to Trigger Table — Design Spec

**Problem:** CLAUDE.md is ~160 lines / ~7KB and loads on every prompt turn. Four sections — "Hook Output Convention", "Hook Error Handling Convention", "Hook Context Hints", and the config key table — are hook-authoring reference material that Claude never needs during normal development turns, wasting an estimated 500–800 tokens per turn.

**Approach:** Move the four verbose sections to new spoke docs in `zie-framework/project/`. Replace them in CLAUDE.md with a single 4-row trigger table pointing to the spoke files. Update `/resync` and `/init` templates to reference new paths. Add a line-count lint rule to `make lint` or CI to enforce ≤80 lines going forward.

**Components:**

- `CLAUDE.md` — remove 4 sections, add trigger table (~75 lines target)
- `zie-framework/project/hook-conventions.md` — new file: Hook Output Convention + Hook Error Handling Convention + Hook Context Hints (moved verbatim)
- `zie-framework/project/config-reference.md` — new file: config key table (moved verbatim)
- `commands/zie-resync.md` — update resync skill to reference new project docs when rescanning
- `templates/CLAUDE.md` — update init template: add trigger table + references to new docs
- `Makefile` — add `check-claudemd-lines` target; wire into `make lint`
- `tests/` — add lint rule test asserting CLAUDE.md ≤80 lines

**Data Flow:**

1. Developer opens Claude — CLAUDE.md loads (~75 lines, ~3.5KB instead of ~7KB)
2. Developer starts writing a hook → sees trigger table row: "Hook conventions → zie-framework/project/hook-conventions.md"
3. Developer reads hook-conventions.md on demand (not loaded every turn)
4. `make lint` runs `check-claudemd-lines` → fails if CLAUDE.md exceeds 80 lines
5. `/resync` regenerates project docs → references `hook-conventions.md` and `config-reference.md` in its knowledge links section

**Edge Cases:**

- CLAUDE.md line count must be measured after any trailing newline (use `wc -l` or Python `len(lines)`)
- `hook-conventions.md` and `config-reference.md` must not appear in the reviewer context bundle (they are reference docs, not decision docs — no changes to ADR-009 bundle loading)
- `/init` template must include trigger table so new projects get the lean CLAUDE.md from day one
- If `/resync` is run before `hook-conventions.md` exists, it must still succeed gracefully (skip reference if file absent)
- Makefile target must not break if CLAUDE.md is absent (e.g., in a fresh clone before `/init`)

**Out of Scope:**

- Trimming any section that Claude actively uses during normal turns (project overview, stack, key rules, dev commands, SDLC commands table)
- Changing the content inside Hook Output Convention or Hook Error Handling Convention (moved verbatim, no edits)
- Adding line-count enforcement to other docs (README, PROJECT.md)
- Automated migration of existing projects (one-time manual operation per project)
