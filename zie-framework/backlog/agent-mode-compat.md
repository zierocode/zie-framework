# agent-mode-compat

## Problem

The `model: sonnet/haiku` frontmatter in agent files and skills is Claude-specific. When running under `glm-5.1:cloud` (or any non-Claude model), the model tier is silently ignored — the session uses whatever model it was started with. More critically, the `--agent` flag and `Skill()` tool invocations may not work correctly on non-Claude model providers. The `/implement` command currently uses `make zie-implement` which invokes `claude --agent zie-framework:zie-implement-mode`, a Claude Code CLI feature that may fail on other providers.

## Motivation

Users on non-Claude models (glm-5.1:cloud, Ollama, etc.) should still be able to use the full pipeline. The `make zie-implement` target breaks on non-Claude providers, and the `model:` frontmatter gives false expectations about model routing.

## Rough Scope

1. **Document non-Claude model limitations** — Add a section to `CLAUDE.md` or `project/context.md` explaining that `model:` frontmatter and `--agent` flag are Claude Code CLI features. On non-Claude providers, `/implement` should be invoked directly (not via `make zie-implement`).
2. **Add fallback invocation in `/implement`** — When `--agent` mode is unavailable (detected by checking if `claude` CLI exists or by catching errors), fall back to running the implement skill directly in the current session without spawning a new agent.
3. **Make `model:` frontmatter optional** — Add a note in agent files that `model:` is a hint, not a requirement. Non-Claude providers ignore it gracefully.
4. **Update Makefile** — Add a `make implement` target that works without `--agent` flag (just runs the skill in the current session).