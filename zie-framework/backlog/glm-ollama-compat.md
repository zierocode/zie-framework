---
tags: [bug]
---

# GLM/Ollama Cloud Compatibility

## Problem

zie-framework has a critical security gap when running through Ollama Cloud with non-Claude models (e.g., glm-5.1:cloud). The safety_check_agent.py hardcodes `claude-haiku-4-5-20251001` as the subagent model (line 87), which doesn't exist in Ollama Cloud. The CLI returns an error message that doesn't contain "BLOCK", causing parse_agent_response() to default to ALLOW — allowing dangerous commands through. Additionally, effort routing frontmatter (effort: low/medium/high) has no effect on non-Claude models, and the safety check agent has no test coverage for model-unavailable scenarios.

## Motivation

Users running Claude Code through Ollama Cloud need the framework to work safely. The safety agent must either use the correct model or fall back to regex correctly when the specified model is unavailable. This was discovered during a full compatibility audit of glm-5.1:cloud.

## Rough Scope

- Fix safety_check_agent.py: read model from env var ANTHROPIC_DEFAULT_HAIKU_MODEL with hardcoded fallback
- Fix safety_check_agent.py: detect model-unavailable error messages and fall back to regex
- Add unit tests for model-unavailable and non-Claude model scenarios
- Add ADR documenting non-Claude model compatibility considerations