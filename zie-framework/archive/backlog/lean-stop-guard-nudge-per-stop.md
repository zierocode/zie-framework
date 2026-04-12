# Backlog: Session-gate stop-guard nudge subprocess calls

**Problem:**
stop-guard.py runs `_run_nudges()` on every Stop event. This includes a
`git log --all -p -- zie-framework/ROADMAP.md | grep` (full patch history pipe)
for each Now lane item, a filesystem mtime scan of all test files, and a ROADMAP
date parse. Stop fires every time Claude finishes a response — potentially dozens
of times per session. The nudges (RED phase duration, coverage staleness, stale
backlog) are session-level signals that don't change turn-by-turn.

**Motivation:**
The `git log --all -p` command pipes the full patch history just to extract a
commit date — an O(history) operation on every Stop. Replacing it with
`git log --all --format="%H %ai" -- zie-framework/ROADMAP.md` eliminates the
patch body (10–100× less output to parse). Adding a session-scoped TTL gate
(~30 min) converts O(stop_events) subprocess calls to O(1) per session.

**Rough scope:**
- Replace `git log --all -p` with `git log --all --format="%H %ai"` in _run_nudges
- Write a "nudge-last-check" marker to project_tmp_path() at first run
- Gate _run_nudges() behind: only fire if marker is absent or older than 30 min
- Add `shlex.quote(slug)` to the grep argument (security fix bundled here)
- Tests: nudge throttle gate, lighter git log format
