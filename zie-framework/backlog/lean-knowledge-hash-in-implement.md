# Backlog: Remove knowledge-hash bang injection from /implement banner

**Problem:**
implement.md lines 13–15 run `!python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now`
as a live bang injection on every /implement invocation. The hash value itself
conveys nothing actionable — it's a fingerprint displayed in the banner. Knowledge
drift is already checked by session-resume.py at session start (fire-and-forget
subprocess) and surfaces in /status output.

**Motivation:**
The bang injection runs knowledge-hash.py (which does an rglob + hash computation
across all project files) on every /implement run. This adds subprocess overhead and
~50–100 tokens of hash output to the banner context. Remove it from /implement;
rely on session-resume drift detection + /status for drift visibility.

**Rough scope:**
- Remove the `!python3 ... knowledge-hash.py --now` bang line from implement.md banner
- Verify session-resume.py already covers the drift detection use case (it does)
- Tests: structural test asserting implement.md does not contain knowledge-hash invocation
