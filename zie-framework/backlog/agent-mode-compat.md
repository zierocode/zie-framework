---
tags: [feature]
---

# agent-mode-compat — Non-Claude Model Compatibility

## Problem

The `model:` frontmatter in agent files and skills is Claude Code-specific. When running under non-Claude models (glm-5.1:cloud, Ollama), the model tier hint is silently ignored. More critically, the `--agent` flag may be unavailable on non-Claude providers.

## Motivation

Users on non-Claude models should still be able to use the full pipeline. Documentation and fallback invocation patterns needed.

## Rough Scope

- Document non-Claude model limitations in CLAUDE.md
- Add fallback invocation in `/implement` (direct Skill call when --agent unavailable)
- Make `model:` frontmatter optional (hint, not requirement)
- Add `make implement` target without --agent flag

<!-- priority: HIGH -->
<!-- depends_on: none -->
