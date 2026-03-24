# Backlog: PreCompact/PostCompact WIP Preservation

**Problem:**
When Claude Code compacts context (auto or manual), zie-framework loses all
SDLC state — active task, current TDD phase, which files were changed. Claude
must re-discover everything from scratch, wasting turns and causing mistakes.

**Motivation:**
Context compaction is the #1 UX break in long sessions. PreCompact and
PostCompact hook events are specifically designed for this: save state before
compact, restore it after. Without this, every compact resets the SDLC session.

**Rough scope:**
- New hook: `hooks/sdlc-compact.py` handling both PreCompact and PostCompact
- PreCompact: write snapshot JSON to project tmp (active task, git branch,
  last-modified files, current TDD phase) using `safe_write_tmp()`
- PostCompact: read snapshot, output `additionalContext` with full SDLC
  state injected back into Claude's context
- Register in `hooks/hooks.json` for both events
- Tests: snapshot roundtrip, missing snapshot graceful handling
