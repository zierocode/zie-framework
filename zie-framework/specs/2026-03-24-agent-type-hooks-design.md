---
approved: true
approved_at: 2026-03-24
backlog: backlog/agent-type-hooks.md
---

# type:"agent" Hooks for Smart Safety Validation — Design Spec

**Problem:** `safety-check.py` relies on brittle hardcoded regex patterns that
miss command variants (multi-space, Unicode, obfuscation) and require manual
updates whenever new dangerous patterns emerge.

**Approach:** Introduce a `type: "agent"` hook variant for `PreToolUse:Bash`
that delegates safety evaluation to a Claude Haiku subagent, which evaluates
the command in context and returns a structured allow/deny JSON decision. The
feature is controlled by a `safety_check_mode` config flag so the existing
regex hook remains the default and fallback. When mode is `"both"`, both hooks
run and their decisions are logged for A/B analysis; the regex result is
authoritative for blocking to guarantee no latency regression in deny cases.

**Components:**
- `hooks/safety-check-agent.py` — new agent hook script
- `hooks/safety-check.py` — existing hook; add mode-dispatch logic and A/B
  logging path
- `hooks/hooks.json` — add second `PreToolUse:Bash` hook entry for
  `safety-check-agent.py` (active only when mode is `agent` or `both`)
- `templates/.config` — add `safety_check_mode: "regex"` default field
- `hooks/utils.py` — add `load_config()` helper if not already present (used
  by both hooks to read `.config`)
- `tests/test_safety_check_agent.py` — unit tests for new hook
- `tests/test_safety_check.py` — extend with mode-dispatch tests

**Data Flow:**

1. User submits a Bash command; Claude Code fires `PreToolUse` for the `Bash`
   tool and passes the event JSON on stdin to each registered hook in sequence.
2. Both `safety-check.py` and `safety-check-agent.py` receive the same event.
   Each reads `safety_check_mode` from `.config` (path: `$CLAUDE_PROJECT_ROOT/.config`
   or CWD fallback). If the mode does not include their role they exit 0
   immediately.
   - `"regex"` — only `safety-check.py` runs (default, current behavior).
   - `"agent"` — only `safety-check-agent.py` runs; regex hook exits early.
   - `"both"` — both run; see step 5 for arbitration.
3. `safety-check-agent.py` constructs the agent prompt:
   ```
   You are a safety validator for a developer workstation.
   Evaluate the following Bash command and decide if it is dangerous.

   Dangerous = any of:
   - Destructive/irreversible filesystem operations (rm -rf on system/home paths,
     wiping non-build directories)
   - Force push to main/master branch
   - Dropping or truncating databases without explicit migration context
   - --no-verify bypassing hooks

   Command: <command>

   Respond ONLY with valid JSON: {"decision": "allow"|"deny", "reason": "<string>"}
   Do not include any other text.
   ```
4. `safety-check-agent.py` invokes the subagent using the Claude Code
   `type: "agent"` hook mechanism with `model: "haiku"` and `timeout: 10s`.
   The agent's stdout is captured and parsed as JSON.
5. Decision arbitration:
   - Mode `"agent"`: use agent decision directly. If agent returns `deny`,
     print `[zie-framework] BLOCKED (agent): <reason>` and `sys.exit(2)`.
     If agent returns `allow`, exit 0.
   - Mode `"both"`: log both decisions to
     `$CLAUDE_PROJECT_ROOT/.zie-framework/safety-ab.jsonl` as a single
     newline-delimited JSON record `{"ts": ..., "command": ..., "regex": "allow"|"deny",
     "agent": "allow"|"deny", "agent_reason": ...}`. Use regex decision for
     the actual block/allow outcome (regex is authoritative in `"both"` mode).
6. Timeout handling: if the agent call exceeds 10 s or raises any exception,
   `safety-check-agent.py` falls back to regex evaluation by importing and
   calling the check logic from `safety-check.py` directly (or re-running it
   as a subprocess). Logs `[zie-framework] safety-check-agent: timeout/error,
   fell back to regex` to stderr. Always exits 0 or 2 — never raises.
7. Output protocol: blocked commands print one `[zie-framework] BLOCKED ...`
   line to stdout and exit 2. Allowed commands produce no output and exit 0.
   Warnings (from WARNS list in regex hook) remain non-blocking and are always
   printed by whichever hook is active.

**Edge Cases:**

- **Malformed agent JSON response:** catch `json.JSONDecodeError`; fall back to
  regex. Log the raw response to stderr for debugging.
- **Agent returns unexpected `decision` value** (not `"allow"` or `"deny"`):
  treat as parse failure and fall back to regex.
- **`.config` missing or `safety_check_mode` key absent:** default to `"regex"`;
  agent hook exits 0 immediately. No crash.
- **Agent hook called but Claude Code agent execution not available** (e.g.,
  run in a context without subagent support): the invocation will raise an
  exception caught by the outer guard; fall back to regex.
- **`"both"` mode, `.zie-framework/` log directory missing:** create it with
  `mkdir -p` before writing; if that fails, skip logging and continue — do not
  block the command over a logging failure.
- **Command is empty string:** both hooks already exit 0 early (matches
  existing `safety-check.py` guard).
- **Concurrent A/B log writes** (multiple hooks firing simultaneously): use
  `open(..., 'a')` with a single `write()` call; POSIX append is atomic for
  small writes — acceptable for a local log file.
- **Agent returns `deny` for a benign command** (false positive): in `"agent"`
  mode this blocks the command; user can switch to `"regex"` or `"both"` while
  the agent prompt is tuned. The A/B log in `"both"` mode is the primary
  diagnostic tool for false-positive analysis.
- **ReDoS / regex complexity in fallback:** the existing `safety-check.py`
  BLOCKS/WARNS lists are already guarded against ReDoS by design (simple
  anchored patterns). No change needed.

**Out of Scope:**

- Replacing the regex hook entirely — it remains the default and the fallback.
- Agent evaluation for non-Bash tools (Edit, Write, etc.).
- Surfacing A/B log analysis to the user automatically — that is a separate
  backlog item.
- Configuring the agent model beyond `haiku` — model is hardcoded in this
  iteration.
- Per-project custom danger definitions in the agent prompt — prompt is fixed
  in this iteration.
- CI/CD integration or remote logging of safety decisions.
- Modifying the `WARNS` (non-blocking) list — those stay regex-only.
