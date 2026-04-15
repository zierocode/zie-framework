# Backlog: Skills !`cmd` Bash Injection for Live Context

**Problem:**
Skills like zie-implement and zie-status require Claude to run Bash commands
(git log, git status, cat ROADMAP) at the start of every invocation to gather
current state. This adds 3-5 tool call turns before any real work begins.

**Motivation:**
Skills support `!`command`` syntax: shell commands that run before the skill
content is sent to Claude, with output replacing the placeholder inline. Claude
receives fully-rendered context (actual git log, actual ROADMAP state) with zero
extra tool calls.

**Rough scope:**
- Add bash injection to zie-implement: `!`git log -5 --oneline``,
  `!`git status --short``, `!`python3 hooks/knowledge-hash.py --now 2>/dev/null``
- Add bash injection to zie-status: `!`cat zie-framework/ROADMAP.md | head -30``
- Add bash injection to zie-retro:
  `!`git log $(git describe --tags --abbrev=0)..HEAD --oneline``
- Use `${CLAUDE_SKILL_DIR}` for script paths so they work regardless of CWD
- Keep injections fast (< 500ms) — no network calls
- Tests: skill content renders with substituted values, failed command graceful
