# spec: release-non-claude-fallback

## Problem

The `/implement` command has a non-Claude advisory and a `make implement-local` fallback. The `/release` command has neither — `make zie-release` silently fails on non-Claude providers. Additionally, inline `<!-- model: sonnet reasoning -->` comments in `release.md` and `impl-reviewer/SKILL.md` imply a routing mechanism that non-Claude models cannot fulfill.

## Spec

### 1. Non-Claude Advisory in `/release` Command

In `commands/release.md`, add a pre-flight advisory immediately before the main steps (after the header block, before step 1), mirroring the existing advisory in `commands/implement.md:17`:

```markdown
> **Non-Claude models:** If running on a non-Claude provider (e.g. minimax-m2.7:cloud),
> invoke `/release` directly — do NOT use `make zie-release`. The `--agent` flag
> is a Claude Code CLI feature unavailable on other providers.
```

### 2. `make release-local` Target

In `Makefile`, after the existing `implement-local` target (~line 61), add:

```make
release-local: ## Run /release directly in current session (non-Claude fallback)
	@echo "Use: /release"
	@echo "Do NOT use 'make zie-release' on non-Claude providers."
```

### 3. Remove Inline `<!-- model: sonnet reasoning -->` Comments

Three locations:

- `commands/release.md:126` — remove `<!-- model: sonnet reasoning: version suggestion ...-->`
- `commands/release.md:143` — remove `<!-- model: sonnet reasoning: narrative rewrite ...-->`
- `skills/impl-reviewer/SKILL.md:46` — remove `<!-- model: sonnet escalation note: ... escalate to sonnet reasoning. -->`

Replace each with a plain-text note that doesn't imply model-tier routing:
- `release.md:126` → `<!-- NOTE: version suggestion requires judgment about breaking changes -->`
- `release.md:143` → `<!-- NOTE: narrative rewrite produces human-readable commit history -->`
- `impl-reviewer/SKILL.md:46` → `<!-- NOTE: escalate to a reasoning-capable model if available -->`

### 4. Verify Env Var Hardening (Already Handled)

`hooks/subagent-context.py` does not read `CLAUDE_SESSION_ID` or `CLAUDE_PLUGIN_DATA` — it gets session info from the event JSON. No changes needed. This item is confirmed as already handled by the existing `session_id` graceful absence branch.

## Out of Scope

Other `commands/` or `skills/` files beyond `release.md` and `impl-reviewer/SKILL.md`. If similar `<!-- model: -->` comments exist elsewhere, they will be handled in a future audit.

## Verification

- [ ] `commands/release.md` contains non-Claude advisory in pre-flight section
- [ ] `Makefile` contains `release-local` target
- [ ] `commands/release.md` has no `<!-- model: sonnet reasoning -->` comments
- [ ] `skills/impl-reviewer/SKILL.md` has no `<!-- model: sonnet escalation note -->` comment
- [ ] `hooks/subagent-context.py` env var handling — verified already correct (no action needed)
- [ ] `make test-unit` passes
