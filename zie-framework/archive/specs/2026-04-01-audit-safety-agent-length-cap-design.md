---
slug: audit-safety-agent-length-cap
status: draft
date: 2026-04-01
---

# Spec: Add Command Length Cap to safety_check_agent invoke_subagent

## Problem

`hooks/safety_check_agent.py` lines 46–59 — `invoke_subagent()` passes the raw
shell command string directly into a `claude --print` subprocess prompt with no
length limit. An unusually long command (e.g. a heredoc payload, a long
generated script, or an injected string) produces an oversized prompt, which
can cause slow agent evaluation, unexpected token-limit behaviour, or inflated
API cost.

Exposure is limited in practice:

- The default `safety_check_mode` is `"regex"` — `invoke_subagent` is never
  called in that mode.
- In `"both"` mode the regex pre-filter runs first; only commands that pass
  regex reach the agent.

However, in `"agent"` mode there is no guard at all, and any command of
arbitrary length is forwarded verbatim.

## Proposed Solution

Add a `MAX_COMMAND_LEN = 4096` module-level constant to
`hooks/safety_check_agent.py`. At the top of `invoke_subagent()`, before
building the prompt string, truncate the command if it exceeds this limit and
append a visible marker so the subagent knows it is evaluating a partial
command:

```python
MAX_COMMAND_LEN = 4096

def invoke_subagent(command: str, timeout: int = 30) -> str:
    if len(command) > MAX_COMMAND_LEN:
        original_len = len(command)
        command = command[:MAX_COMMAND_LEN] + f"\n[truncated at {MAX_COMMAND_LEN} chars — original len: {original_len}]"
        print(
            f"[zie-framework] safety_check_agent: command truncated to {MAX_COMMAND_LEN} chars (was {original_len})",
            file=sys.stderr,
        )
    prompt = (
        "You are a safety agent for a developer terminal. "
        ...
    )
```

The truncation marker is included in the prompt body so the subagent can
factor it into its ALLOW/BLOCK decision. The stderr log provides observability
for developers who wonder why an agent evaluation fired on a short snippet.

No changes to the outer `evaluate()` function or the two-tier error handling.
No changes to `safety-check.py` (regex mode, unaffected).

## Acceptance Criteria

- [ ] AC1: `MAX_COMMAND_LEN = 4096` constant exists at module level in `hooks/safety_check_agent.py`.
- [ ] AC2: `invoke_subagent()` truncates `command` to `MAX_COMMAND_LEN` chars before constructing the prompt when `len(command) > MAX_COMMAND_LEN`.
- [ ] AC3: The truncated string ends with `"\n[truncated at 4096 chars — original len: N]"` where N is the original length.
- [ ] AC4: A `[zie-framework] safety_check_agent: command truncated to 4096 chars (was N)` message is printed to `stderr` when truncation occurs.
- [ ] AC5: Commands at or below `MAX_COMMAND_LEN` chars pass through unchanged with no stderr output and no truncation marker in the prompt.
- [ ] AC6: Unit tests cover: (a) command exactly at limit — no truncation; (b) command one char over limit — truncation fires with correct marker and stderr log; (c) very long command (e.g. 10 000 chars) — truncated correctly.
- [ ] AC7: `make test-ci` passes with no regressions.

## Out of Scope

- Changing the truncation limit value after implementation (can be a future config key if needed).
- Exposing `MAX_COMMAND_LEN` as a config key in `zie-framework/.config`.
- Modifying the regex pre-filter in `safety-check.py` or `_regex_evaluate()`.
- Changing behaviour when the subagent itself times out or errors (existing fallback to `_regex_evaluate` is unchanged).
- Truncating the prompt template text itself — only the user-supplied `command` argument is capped.
