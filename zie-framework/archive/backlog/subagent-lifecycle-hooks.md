# Backlog: SubagentStop Capture + Resume Subagent Pattern

**Problem:**
When reviewer subagents finish, their findings disappear. There's no mechanism
to (1) capture what a research subagent learned for the retro, or (2) resume
a reviewer in the same context for a follow-up question.

**Motivation:**
`SubagentStop` fires when any subagent completes and receives the agent's last
message. Logging this to a session file enables retro analysis. The resume
pattern (Claude uses SendMessage with agent ID) allows continuing a reviewer
without starting fresh — saving context re-load time.

**Rough scope:**
- New hook: `hooks/subagent-stop.py` (SubagentStop event, async: true)
- Capture: agent_id, agent_type, last_assistant_message → append to
  `project_tmp_path("subagent-log")` as JSONL
- Register with `async: true` (non-blocking — just logging)
- Update /zie-retro to read the subagent log for "what agents were used this
  session" summary
- Document the resume pattern in zie-implement: how to @-mention agent ID
  for follow-up reviews
- Tests: log written correctly, async non-blocking, missing tmp path graceful
