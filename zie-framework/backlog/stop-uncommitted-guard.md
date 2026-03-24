# Backlog: Stop Hook — Uncommitted Work Guard

**Problem:**
When Claude finishes a response (`Stop` event), it may have just written feature
code or tests without committing. The session could end or compact, losing track
of what was done. Currently `session-cleanup.py` only deletes /tmp files on Stop.

**Motivation:**
Stop hooks support `decision: "block"` with a reason that gets fed back to
Claude, causing it to continue. An uncommitted-work guard checks `git status`
and blocks the Stop if implementation files are staged/unstaged — prompting
Claude to commit before considering the turn done.

**Rough scope:**
- Update `hooks/session-cleanup.py` or create separate `hooks/stop-guard.py`
- On Stop: run `git status --short`, filter for implementation files
  (hooks/*.py, tests/*.py, commands/*.md, skills/**/*.md)
- If uncommitted files found: `decision: "block"`, reason: list files +
  "Commit this work before ending: git add -A && git commit -m 'feat: ...'"
- Guard: only block once per response (check `stop_hook_active` field)
- Tests: uncommitted files trigger block, clean tree exits 0, stop_hook_active
  guard prevents infinite loop
