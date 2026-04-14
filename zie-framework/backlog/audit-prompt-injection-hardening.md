---
tags: [bug]
---

# Harden Safety Check Agent Against Prompt Injection

## Problem

`safety_check_agent.py` passes user-provided command text to `claude --print --model` after partial sanitization (XML tag escaping, Unicode bidi strip). The sanitization doesn't neutralize all prompt injection vectors — role-playing prompts and `</command>` injection within the command body can bypass the check. External validation (Claude Code plugin security research) identifies prompt injection as a top-3 threat for AI agent plugins.

## Motivation

This is the primary safety gate for Bash command execution. A bypass could allow arbitrary command execution without user confirmation.

## Rough Scope

- Add prompt injection pattern blocklist (role-playing keywords, instruction injection patterns)
- Add output validation — reject agent responses that don't match expected safety-check format
- Consider input length cap for command text passed to the agent
- Add regression tests for known injection vectors