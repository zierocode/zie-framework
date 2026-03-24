# Backlog: ConfigChange Hook — Detect CLAUDE.md / Settings Drift

**Problem:**
When CLAUDE.md or .claude/settings.json changes during a session (another
terminal, git pull, /zie-resync), Claude Code has already loaded the old
instructions. The agent continues with stale rules until the session restarts.

**Motivation:**
`ConfigChange` fires when any settings file changes. It can inject
`additionalContext` or block with a reason. Detecting CLAUDE.md changes
and notifying Claude (or triggering a soft reload via `additionalContext`)
keeps the agent's instructions in sync with the actual project state.

**Rough scope:**
- New hook: `hooks/config-drift.py` (ConfigChange event)
- Matcher: `project_settings|user_settings` (watch .claude/ changes)
- On change: check if file_path is CLAUDE.md or settings.json
- Output `additionalContext`: "CLAUDE.md has been updated. Re-read it with
  Read('.claude/CLAUDE.md') before continuing."
- Also check if zie-framework/.config changed → suggest /zie-resync
- Tests: CLAUDE.md change triggers context, settings.json change triggers,
  unrelated config change is quiet
