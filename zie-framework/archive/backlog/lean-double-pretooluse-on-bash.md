# Backlog: Merge safety_check_agent.py into safety-check.py (eliminate per-Bash config read)

**Problem:**
hooks.json registers two PreToolUse matchers: safety-check.py fires on
`Write|Edit|Bash`; safety_check_agent.py fires on `Bash` only. Every Bash invocation
runs both. The inactive one (based on safety_check_mode config) does a config read
then exits. In default "regex" mode: safety_check_agent.py does a config read + exit
on every single Bash call. This is a subprocess spawn + Python startup + config read
that produces zero output, on every Bash.

**Motivation:**
ADR-043 consolidated PreToolUse hooks but left these two separate. The agent safety
checker should be an internal dispatch path inside safety-check.py, not a separate
process. Eliminates one Python startup + config read per Bash call.

**Rough scope:**
- Import safety_check_agent logic into safety-check.py as an internal function
- Add internal dispatch: if mode == "agent" or "both" → call agent check inline
- Remove safety_check_agent.py as a standalone hook registration from hooks.json
- Keep safety_check_agent.py as a module (imported by safety-check.py)
- Tests: verify single hook fires, mode dispatch works for all three modes
