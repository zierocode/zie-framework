---
approved: true
approved_at: 2026-04-11
backlog:
---

# Conversation Capture — Design Spec

**Problem:** After a design conversation where the brainstorm skill was NOT explicitly invoked, Zie must manually re-state the full context before running `/sprint`. There is no mechanism to carry implicit design conversation decisions into the pipeline.

**Approach:** Three components: (A) `design-tracker.py` UserPromptSubmit hook detects design-intent signals and sets a session flag; (B) Stop hook reads that flag and writes `.zie/handoff.md` only when brainstorm skill was not already invoked; (C) `/brief` command reviews the artifact, and `/sprint` reads it automatically.

**Relationship to brainstorming-skill spec:** The brainstorm skill is the **primary** write path for `.zie/handoff.md` (explicit sessions). This spec is the **secondary** write path (implicit sessions). The Stop hook checks for a `brainstorm-active` flag and skips write if brainstorm skill already ran — brainstorm takes precedence. There is never a write collision.

**Out of Scope:** brainstorm skill behavior, .zie/handoff.md format decisions (defined in brainstorming-skill spec), /sprint implementation details beyond handoff.md detection.

**`.zie/` Directory Convention:**
- Location: `$CWD/.zie/` (project root)
- Must be added to `.gitignore` as part of this feature's implementation
- Created by Stop hook on first write if absent

**Components:**
- `hooks/design-tracker.py` — UserPromptSubmit hook (async: true); detects design-intent, writes session flag
- `hooks/stop-capture.py` — Stop hook (`async: false`); reads flag, writes handoff.md if brainstorm-active not set. Must be synchronous — handoff.md must be flushed before the session record closes, so async: true would create a race where the file may not exist when /sprint reads it next session.
- `hooks/hooks.json` — add design-tracker.py to UserPromptSubmit array; add stop-capture.py to Stop array
- `.gitignore` — add `.zie/` entry
- `commands/brief.md` — new `/brief` command; reads handoff.md, displays summary
- `commands/sprint.md` — enhanced to auto-read `.zie/handoff.md` when present

**Session State Files (using `project_tmp_path()` from `utils_io.py`):**
- `project_tmp_path("design-mode", project)` — written by design-tracker.py when design intent detected
- `project_tmp_path("brainstorm-active", project)` — written by brainstorm skill (read-only here); if present, stop-capture.py skips write

**Data Flow:**

*A — design-tracker.py (UserPromptSubmit, async: true):*
1. Read message from event
2. Detect design-intent signals: keywords (design, spec, build, feature, improve, "discuss → sprint"), consecutive design turns (≥3), multi-topic exploration
3. On detection: write `project_tmp_path("design-mode", project)` flag file
4. Non-blocking: async: true, Tier 1 outer guard

*B — stop-capture.py (Stop hook):*
1. Check `project_tmp_path("brainstorm-active", project)` — if exists: skip (brainstorm skill handled it), exit 0
2. Check `project_tmp_path("design-mode", project)` — if not exists: skip (no design conversation), exit 0
3. Create `$CWD/.zie/` if absent
4. Write `$CWD/.zie/handoff.md` (same format as brainstorming-skill spec, with `source: design-tracker`)
5. Delete `project_tmp_path("design-mode", project)` flag (cleanup)

*handoff.md format (identical to brainstorm spec format):*
```markdown
---
captured_at: YYYY-MM-DDTHH:MM:SSZ
feature: <extracted or inferred name>
source: design-tracker
---

## Goals
- <bullet per goal>

## Key Decisions
- <bullet per design decision made>

## Constraints
- <bullet per constraint mentioned>

## Open Questions
- <bullet per unresolved question>

## Context Refs
- <file paths or commands mentioned as relevant>

## Next Step
/sprint <feature-name>
```

*C — /brief + /sprint:*
1. Zie runs `/brief` → reads `$CWD/.zie/handoff.md` → displays formatted summary
2. User confirms → `/sprint` invoked with handoff content as brief
3. `/sprint` detects `$CWD/.zie/handoff.md` presence → reads it → populates spec frontmatter
4. After sprint completes: `/sprint` deletes `$CWD/.zie/handoff.md`
5. If no handoff.md: `/sprint` behaves as before (prompts for topic)

**Error Handling:**
- design-tracker.py: async: true, Tier 1 outer guard (bare except → exit 0), never blocks Claude
- stop-capture.py: Tier 1 outer guard; if .zie/ unwriteable → log warning to stderr, exit 0
- `/brief` with no handoff.md: prints "No active design brief — run a design conversation first"
- `/sprint` with malformed handoff.md: falls back to manual prompt mode + warns

**Testing (`tests/unit/test_design_tracker.py`, `tests/unit/test_stop_capture.py`):**
- Unit: design-tracker writes design-mode flag when signals detected
- Unit: design-tracker exits 0 without writing flag when no signals present
- Unit: stop-capture skips write when brainstorm-active flag present
- Unit: stop-capture skips write when design-mode flag absent
- Unit: stop-capture writes handoff.md with correct structure when design-mode active
- Unit: stop-capture deletes design-mode flag after writing handoff.md
- Unit: handoff.md frontmatter fields populated correctly (source: design-tracker)
- Unit: stop-capture exits 0 on malformed event (@pytest.mark.error_path)
- Integration: full "discuss → /brief → /sprint" flow (requires live session)
- Regression: existing /sprint tests pass unchanged (manual-prompt path)
