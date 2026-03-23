# Backlog: type:"agent" Hooks for Smart Validation (Replace Hardcoded Patterns)

**Problem:**
`safety-check.py` uses hardcoded regex patterns to block dangerous commands.
Patterns are brittle — they miss variants (multi-space, Unicode, obfuscation)
and need manual updates. The ReDoS guard exists because patterns got too complex.

**Motivation:**
Claude Code supports `type: "agent"` hooks: a subagent (using Explore model)
evaluates the proposed action and returns allow/deny as JSON. An agent-based
safety check understands context ("rm -rf ./build is fine in CI, dangerous in
/home"), handles variants naturally, and never needs regex updates.

**Rough scope:**
- Add `type: "agent"` alternative alongside `type: "command"` safety-check
  (feature flag in .config: `safety_check_mode: "regex"|"agent"|"both"`)
- Agent prompt: "Is this Bash command dangerous? Command: $ARGUMENTS. Reply
  JSON: {decision: allow|deny, reason: string}. Dangerous = destructive/
  irreversible ops on system files, force push to main, dropping databases."
- Keep regex safety-check as fallback if agent hook times out
- Agent hook uses `model: haiku`, `timeout: 10s`
- A/B comparison: log both regex and agent decisions for analysis
- Tests: agent hook output parsing, timeout fallback, config flag
