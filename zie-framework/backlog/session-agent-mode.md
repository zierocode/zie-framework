# Backlog: Session-Wide Agent Mode (--agent Flag Integration)

**Problem:**
zie-framework sessions default to the standard Claude Code system prompt. There's
no way to run an entire session in "implement mode" (TDD-focused, all permissions
pre-approved for SDLC operations) or "audit mode" (read-only, analysis focused).

**Motivation:**
Claude Code supports `--agent <name>` to start a session where the main thread
takes on a custom agent's system prompt, tool restrictions, and model. A
`zie-implement-mode` agent pre-configures the session: TDD focus, common tools
auto-approved, SDLC context always injected. Users run `claude --agent
zie-framework:zie-implement-mode` for a fully configured SDLC session.

**Rough scope:**
- Create `agents/zie-implement-mode.md` — system prompt: TDD-focused, knows
  the SDLC pipeline; tools: all; permissionMode: acceptEdits; preloads
  tdd-loop + test-pyramid skills
- Create `agents/zie-audit-mode.md` — system prompt: analysis focused; tools:
  Read/Grep/Glob/WebSearch only; permissionMode: plan
- Add `settings.json` at plugin root with `"agent": "zie-implement-mode"`
  as the recommended default
- Document: `claude --plugin-dir . --agent zie-framework:zie-implement-mode`
  for dev sessions
- Tests: agent files parse, system prompt injected, tool restrictions work
