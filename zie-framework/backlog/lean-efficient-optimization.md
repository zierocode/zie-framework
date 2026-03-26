# Lean & Efficient Optimization

## Problem

zie-framework consumes ~70% of every Claude Code session's token budget on framework overhead (hooks, context injection, git operations) rather than actual user work. A typical 15-message debug session with 8 file edits incurs ~12,110 tokens of framework overhead vs ~5,000 tokens of actual work. zie-audit command costs 50K–200K tokens per run (Opus + 5 parallel agents + 25 WebSearch queries), potentially consuming 50% of monthly credit budget on a single audit. Multiple redundant ROADMAP.md disk reads (6–8 per session), uncached git subprocess calls, and oversized commands (zie-implement.md: 351 lines, zie-audit.md: 330 lines) multiply this overhead.

## Motivation

Zie wants zie-framework to remain lean, fast, and enterprise-grade — but current credit consumption makes it economically inefficient for production use. Optimizing token consumption will:

1. **Reduce monthly Claude Code spend by 40–65%** without sacrificing quality or safety
2. **Speed up commands** — fewer hook invocations, cached data, leaner prompts
3. **Maintain enterprise standards** — parallel execution, safety checks, quality gates remain intact
4. **Enable continuous auditing** — zie-audit becomes cost-effective to run weekly vs quarterly

Target: reduce framework overhead from ~70% to ~40% of session token cost, saving ~5,500 tokens/session and ~170K tokens/audit.

## Rough Scope

### In Scope:
- Hook layer consolidation (merge UserPromptSubmit hooks, cache ROADMAP.md, disable safety_check_agent by default, async wip-checkpoint)
- zie-audit overhaul (5 Opus agents → 3 Sonnet + 1 synthesis pass, effort:high → medium)
- Effort right-sizing (zie-plan, zie-retro, impl-reviewer overly aggressive)
- Parallel agent cap optimization (implement max 3, plan max 2)
- Slim bloated commands (zie-implement, zie-audit reduce line count 50%+)
- Archive old plans directory (1.6 MB bloat)

### Out of Scope:
- Changing SDLC process or quality gates
- Removing safety checks or security validations
- Removing zie-memory integration
- Changing model tier rankings (Haiku for simple, Sonnet for mid, Opus for hard)

### Risk:
- Hook consolidation could mask simultaneous feature contexts (mitigation: session env var)
- Audit dimension consolidation could reduce finding depth (mitigation: Sonnet agents still capable, synthesis pass reviews comprehensively)
