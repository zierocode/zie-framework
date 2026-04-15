---
date: "2026-04-15"
status: approved
slug: audit-prompt-injection-hardening
---

# Implementation Plan: Audit Prompt Injection Hardening

## Steps

1. **Add `INJECTION_BLOCKS` to `utils_safety.py`** — regex list matching role-play / instruction-injection phrases ("ignore above", "disregard previous", "you are now", "return ALLOW", "output BLOCK", "pretend you are", "act as if", "system:"). Compile at import time.

2. **Replace partial XML escaping with full entity escaping in `invoke_subagent`** — change the two `.replace()` calls to a `_escape_for_xml(text)` function that escapes `&`, `<`, `>` to `&amp;`, `&lt;`, `&gt;`. Remove the old `<command>` / `</command>` replace hacks. This makes `</command>` injection structurally impossible.

3. **Add injection-pattern pre-check in `evaluate()`** — before calling `invoke_subagent`, run command through `INJECTION_BLOCKS`. If matched, BLOCK immediately (no agent call needed).

4. **Harden `parse_agent_response`** — change default from `ALLOW` to `BLOCK` when output contains neither keyword. An ambiguous response is safer to reject.

5. **Update `_regex_evaluate`** — add `INJECTION_BLOCKS` to the compiled pattern list so regex fallback also catches injection patterns.

## Tests

- `test_injection_blocklist_catches_role_play` — commands containing "ignore above" or "pretend you are" return exit 2.
- `test_xml_escape_neutralizes_closing_tag` — a command containing `</command>` is escaped so it cannot break out of the XML wrapper.
- `test_parse_agent_response_defaults_block` — empty/unrecognized response returns BLOCK.
- `test_injection_patterns_in_regex_fallback` — injection patterns are caught even when agent is unavailable.
- `test_full_xml_entity_escape` — `&`, `<`, `>` in command text are entity-escaped in the prompt.

## Acceptance Criteria

- AC-1: Any command containing `</command>` is fully entity-escaped before inclusion in the agent prompt.
- AC-2: Commands matching role-play / instruction-injection patterns are BLOCKed before reaching the agent.
- AC-3: `parse_agent_response` returns BLOCK for unrecognized output (no ALLOW/BLOCK keyword).
- AC-4: Injection-pattern blocklist applies in both agent and regex-fallback paths.
- AC-5: All new and existing injection tests pass.