# Backlog: SessionStart CLAUDE_ENV_FILE — Config as Env Vars

**Problem:**
`session-resume.py` injects project config via `additionalContext` text string.
This means config values (test runner, project name, memory enabled) are in the
conversation prose — Claude has to parse them from natural language. They should
be proper environment variables available to every tool call.

**Motivation:**
SessionStart hooks support `CLAUDE_ENV_FILE`: write `export VAR=value` lines
to this file and Claude Code sets those env vars for the session. This is the
correct mechanism for config that every hook and command needs.

**Rough scope:**
- Update `hooks/session-resume.py` to check `$CLAUDE_ENV_FILE` env var
- Write from `.config`: `ZIE_PROJECT`, `ZIE_TEST_RUNNER`, `ZIE_MEMORY_ENABLED`,
  `ZIE_AUTO_TEST_DEBOUNCE_MS` as exported env vars
- Keep `additionalContext` for human-readable state summary (ROADMAP status)
- All other hooks can then read these vars directly without re-parsing .config
- Tests: env file written correctly, missing CLAUDE_ENV_FILE graceful skip
