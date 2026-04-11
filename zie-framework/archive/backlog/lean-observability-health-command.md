# Backlog: Add framework health section to /status output

**Problem:**
/status shows SDLC state (ROADMAP lanes, test health, knowledge sync) but does
not surface framework health: drift log bypass count, hook error history (stopfailure-
log entries), safety_check_mode in effect, last session-learn output, or subagent-stop
log. Hook stderr errors go to stderr but are never aggregated. The only way to know
if a hook is silently failing is to grep /tmp or session logs manually.

**Rough scope:**
- Add a "Framework Health" section to /status output:
  - safety_check_mode in effect (from .config)
  - Last N entries from stopfailure-log (if any)
  - hook error count from last session (if tracked)
  - zie-memory enabled/disabled
  - playwright enabled/disabled + version if enabled
- Read stopfailure-log file (check utils for path) and summarize
- Tests: /status renders Framework Health section; stopfailure-log entries shown
