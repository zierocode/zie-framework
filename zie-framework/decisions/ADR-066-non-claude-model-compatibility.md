---
id: ADR-066
title: Non-Claude model compatibility (env var model resolution + model-unavailable detection)
status: accepted
date: 2026-04-13
---

## Context

zie-framework runs within Claude Code, which supports model tier routing (opus/sonnet/haiku). The `safety_check_agent.py` hardcoded `claude-haiku-4-5-20251001` for its subagent model. When running through Ollama Cloud (or any non-Claude model provider), this model doesn't exist, causing the CLI to return an error. The error message doesn't contain "BLOCK", so `parse_agent_response()` defaults to ALLOW — a critical security gap.

## Decision

1. Read the model name from `ANTHROPIC_DEFAULT_HAIKU_MODEL` env var, falling back to `claude-haiku-4-5-20251001`. This env var is set by Claude Code when mapping model tiers.
2. Detect model-unavailable CLI errors (non-zero returncode + matching substrings in stdout/stderr) and raise `RuntimeError`, which triggers `evaluate()`'s existing regex fallback.
3. Effort frontmatter (`effort: low/medium/high`) is a no-op for non-Claude models — documented but not actionable.

## Consequences

- **Positive:** Safety check works correctly with any model provider (Ollama Cloud, native Claude, etc.)
- **Positive:** No changes to `evaluate()` control flow — leverages existing except clause
- **Negative:** Substring matching for error detection is brittle across CLI versions — but regex fallback provides safety net
- **Negative:** Effort routing has no effect on non-Claude models — this is accepted as a known limitation