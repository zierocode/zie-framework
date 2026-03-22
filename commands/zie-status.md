---
description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
allowed-tools: Read, Bash, Glob
---

# /zie-status — Show current SDLC state

Show a concise snapshot of where the project is right now. No LLM reasoning needed — just read files and print.

## Steps

1. **Check initialization**: if `zie-framework/` does not exist → print "Not initialized. Run /zie-init first." and stop.

2. **Read files**:
   - `zie-framework/.config` → project_type, test_runner, has_frontend, playwright_enabled
   - `zie-framework/ROADMAP.md` → Now / Next / Done sections
   - `VERSION` → current version
   - `zie-framework/specs/` → list files, sort by date
   - `zie-framework/plans/` → list files, find most recent

3. **Find active plan**: most recent file in `zie-framework/plans/` where ROADMAP.md "Now" section is not empty.

4. **Check test health**:
   - Look for `.pytest_cache/` or `test-results/` → get last run timestamp
   - Check if any test files modified more recently than last run → "stale"

5. **Print status block**:
   ```
   ┌─ zie-framework status ──────────────────────────────────
   │ Project : <directory name> (<project_type>)
   │ Version : <VERSION>
   │ Brain   : <enabled|disabled>
   │
   │ ROADMAP ── Now  : <item count> in progress
   │            Next : <item count> queued
   │            Done : <item count> shipped
   │
   │ Active  : <first Now item or "nothing in progress">
   │ Plan    : <zie-framework/plans/latest.md or "no active plan">
   │
   │ Tests   : unit        <✓ pass | ✗ fail | ? stale | n/a>
   │           integration <✓ pass | ✗ fail | ? stale | n/a>
   │           e2e         <✓ pass | ✗ fail | ? stale | n/a (no frontend)>
   └──────────────────────────────────────────────────────────

   Suggestions:
   → <context-appropriate next command>
   ```

6. **Suggestions logic** (pick the most relevant):
   - Nothing in ROADMAP Now → "Start a feature: /zie-idea"
   - Active plan exists, tasks incomplete → "Continue: /zie-build"
   - Tests stale or failing → "Fix tests: /zie-fix"
   - All tasks in plan complete → "Ready to ship: /zie-ship"
   - Always available: "/zie-status | /zie-idea | /zie-build | /zie-fix | /zie-ship | /zie-retro"

## Notes
- Fast — no LLM, no network calls
- Safe to run anytime, even mid-session
