# Backlog: Plugin settings.json + CLAUDE_PLUGIN_DATA Persistent Storage

**Problem:**
zie-framework ships no default settings and has no persistent storage separate
from /tmp. Projects using the plugin get no default configuration, and any data
that should survive session restarts (e.g. review patterns learned) is lost.

**Motivation:**
Plugins support `settings.json` at the plugin root to ship defaults (currently
only `agent:` key is supported — activates a plugin agent as default). Plugins
also have `$CLAUDE_PLUGIN_DATA` env var pointing to a per-plugin persistent
directory. This enables storing accumulated knowledge outside /tmp.

**Rough scope:**
- Create `settings.json` at plugin root with an `agent:` field if/when a
  default agent is defined (zie-implement-mode agent, for example)
- Update hooks to use `$CLAUDE_PLUGIN_DATA` for data that should persist
  beyond sessions (review pattern cache, subagent log archive)
- Document the distinction: `/tmp` for session state, `CLAUDE_PLUGIN_DATA`
  for cross-session data
- Update `safe_write_tmp()` or add `safe_write_persistent()` utility
- Tests: CLAUDE_PLUGIN_DATA path used correctly, fallback if env var missing
