---
adr: 000
title: ADR Summary (ADR-001 to ADR-030)
status: Compressed
date: 2026-04-03
---

# ADR Summary — ADR-001 to ADR-030

Compressed on 2026-04-03. 30 ADRs → summary table.

| ADR | Title | Decision | Status |
|-----|-------|----------|--------|
| ADR-001 | Reviewer Skills as Dispatched Subagents | Fresh subagents with binary verdict checklist; max 3 iterations. | Accepted |
| ADR-002 | markdownlint Pre-commit Gate | markdownlint-cli2 on staged .md files; MD013 line length = 120. | Accepted |
| ADR-003 | Commands Are the Control Plane, Skills Are Execution | Commands own pipeline transitions; skills execute within one stage, never auto-advance. | Accepted |
| ADR-004 | Spec Approval State Tracked via Frontmatter | spec-reviewer approval → `approved: true` frontmatter; /plan filters by flag. | Accepted |
| ADR-005 | Hybrid Release — SDLC Gates + Project-Defined Publish | Release: SDLC layer (gates + bump) + project layer (git ops + publish). | Accepted |
| ADR-006 | Reviewer Context Bundles | 3-phase: load context bundle → checklist → cross-reference. | Accepted |
| ADR-007 | research_profile as Audit Intel Layer | Build research_profile from manifests; all audit agents + WebSearch adapt from it. | Accepted |
| ADR-008 | Shared Hook Utility Module (hooks/utils.py) | `hooks/utils.py` stdlib-only; exports parse_roadmap_now() + project_tmp_path(). | Accepted |
| ADR-009 | Hook __main__ Guard for Direct Unit Testing | `if __name__ == '__main__':` guard; module-scope functions for direct pytest import. | Accepted |
| ADR-010 | safe_write_tmp() Hard-Fails on Symlink Detection | `safe_write_tmp()` checks `is_symlink()` before writing; logs WARNING, never raises. | Accepted |
| ADR-011 | find_matching_test() OSError Guards at Every Filesystem Call | `try/except OSError` at each filesystem call in `find_matching_test()`. | Accepted |
| ADR-012 | Tiered Model Routing — haiku / sonnet / opus | Three-tier routing: opus+high for zie-audit, sonnet+high/medium for design/plan/impl, haiku+low for checklist/reviewer tasks. | Accepted |
| ADR-013 | Plugin-Bundled MCP Server for Zero-Setup Brain Integration | Ship `.claude-plugin/.mcp.json` to auto-register `zie-memory` MCP; degrades gracefully when env vars are absent. | Accepted |
| ADR-014 | Async impl-reviewer Deferred-Check Polling | Spawn impl-reviewer async after REFACTOR; poll at next iteration; surface issues; max 2 iterations. | Accepted |
| ADR-015 | Hook Test Helpers Must Clear Session-Injected Env Vars | `run_hook()` helpers clear session env vars before test overrides. | Accepted |
| ADR-016 | debounce_ms=0 Means Disabled — Guard with `> 0` | `if debounce_ms > 0` guard prevents APFS timestamp rounding spurious suppression. | Accepted |
| ADR-017 | impl-reviewer Upgraded from haiku/low to sonnet/medium | impl-reviewer → sonnet/medium; spec-reviewer and plan-reviewer remain haiku. | Accepted |
| ADR-018 | utils.py as Canonical Constants and Helpers Library | `utils.py` is the single source of truth for `BLOCKS`, `WARNS`, `SDLC_STAGES`, and `normalize_command`. | Accepted |
| ADR-019 | load_config() Parses JSON Exclusively | `load_config()` uses json.loads() only; eliminates silent INI fallback dropping config values. | Accepted |
| ADR-020 | Async Stop Hooks for Non-Blocking Session End | `session-learn.py` and `session-cleanup.py` marked `"async": true`; `stop-guard.py` remains synchronous. | Accepted |
| ADR-021 | zie-audit Cost Optimization | Replace 5 Opus agents with 3 Sonnet agents + synthesis; ~72% cost reduction; WebSearch 25 → 15. | Accepted |
| ADR-022 | Effort Routing Strategy for Skills and Commands | `effort: high` for spec-design only; others use medium/low; write-plan high → medium. | Accepted |
| ADR-023 | SDLC Artifact Archive Strategy | `archive/` with backlog/specs/plans; `make archive` moves Done-lane items; excluded from reviewer bundles. | Accepted |
| ADR-024 | Git Status Session Cache | Hot-path hooks consult /tmp cache before git subprocesses. | Accepted |
| ADR-025 | ADR Auto-Summarization via /zie-retro | /retro compresses oldest ADRs to ADR-000-summary.md table when count > 30. | Accepted |
| ADR-026 | ROADMAP Done Section Auto-Compaction | `compact_roadmap_done()`: compact Done entries >20 and >6mo old into archive summary. | Accepted |
| ADR-027 | Coverage Gate Lowered to 43% | `--fail-under` 50 → 43; reflects pytest-only baseline without subprocess hooks. | Accepted |
| ADR-028 | Plugin Marketplace as Decoupled Authority | `settings.json` extraKnownMarketplaces is plugin discovery authority; no cross-repo pinning. | Accepted |
| ADR-029 | General-Purpose Agents for Subagents | Spawn general-purpose agents with inline context; eliminates stale-cache failures. | Accepted |
| ADR-030 | Model Routing — Haiku + Sonnet Escalation | Haiku default; judgment steps escalate to Sonnet via `<!-- model: sonnet -->`. | Accepted |
| ADR-031 | ADR Session Cache | write_adr_cache/get_cached_adrs: cache ADR list per session to avoid redundant dir reads. | Accepted |
| ADR-032 | Shared Context Bundle in zie-audit | Build context bundle once in Phase 1; pass to all parallel Phase 2 agents. | Accepted |
| ADR-033 | Parallel Release Gates Fan-Out | Gates 2/3/4 in zie-release run in parallel; only Gate 1 must run first. | Accepted |
| ADR-034 | Phase-Parallel Sprint Orchestration | Sprint: spec all items in parallel, implement sequentially, single batch release+retro. | Accepted |
| ADR-035 | Pure Markdown Sprint Orchestration | /sprint implemented as Markdown command using Agent+Skill tools, not a Python hook. | Accepted |
| ADR-036 | AST Parsing for Hooks with Module-Level Side Effects | Use AST parsing to test hooks that call sys.exit() at module level. | Accepted |
| ADR-037 | Coverage Gate Raised to 48% | --fail-under raised from 43 to 48 after measurement fix. | Accepted |
| ADR-038 | Hook Timing Instrumentation | Hooks emit elapsed_ms to session log for latency diagnostics. | Accepted |
| ADR-039 | Structural Test Assertions | Replace keyword-presence tests with structural assertions (section order, field presence). | Accepted |
| ADR-040 | Input Validation Brace Guard | Add bare brace {} to dangerous compound regex in input-sanitizer. | Accepted |
| ADR-041 | Pre-commit Hook Simplified to Stub | Pre-commit hook is a no-op stub; enforcement moved to CI. | Accepted |
| ADR-042 | utils.py Split into 5 Sub-modules | utils.py split into utils_event, utils_io, utils_safety, utils_roadmap, utils_backlog. | Accepted |
| ADR-043 | Consolidate PreToolUse Hooks | input-sanitizer.py merged into safety-check.py; single PreToolUse hook. | Accepted |
| ADR-044 | Skill Over Agent for Sequential Steps | Use Skill() invocation instead of Agent() for sequential workflow steps to avoid context overhead. | Accepted |
| ADR-045 | ROADMAP Cache mtime-Gate | ROADMAP cache invalidated by file mtime change, not TTL expiry. | Accepted |
| ADR-046 | Subagent Context Scoped by Agent Type | subagent-context.py emits context only for Explore and Plan agents. | Accepted |
| ADR-047 | Retro Inline File Writes | /retro writes ADR + ROADMAP files inline; no background agents for file writes. | Accepted |
| ADR-048 | Shared load-context Skill | load-context skill loads ADRs + context.md once per session; all reviewers reuse bundle. | Accepted |
| ADR-049 | Drift Log NDJSON | SDLC bypass events logged as NDJSON to zie-framework/drift.log. | Accepted |
| ADR-050 | Escape Hatch Over Hard Block | intent-sdlc.py warns and offers escape hatches instead of hard-blocking on no-track state. | Accepted |
| ADR-051 | Command Namespace Flattening | Remove zie- prefix from all commands; invoked as /backlog, /spec, /plan, etc. | Accepted |
| ADR-052 | Bind-Once Session-Scoped Variables | Commands read .config and ROADMAP once per execution; no repeated reads. | Accepted |
| ADR-053 | Self-Enforcement in Framework Not Memory | Fix bad patterns by updating framework spec/skills directly, not by writing zie-memory entries. | Accepted |
| ADR-054 | Inline Reviewer Context Hop Elimination | Reviewer skills load context inline (Phase 1 inlined) instead of invoking reviewer-context as separate hop. | Accepted |
| ADR-055 | Sprint Phase 2 Collapse | Sprint Phase 2 (plan) folded into Phase 1 parallel; spec+plan run as single concurrent wave. | Accepted |
| ADR-056 | Pre-flight Guard Centralization | Canonical pre-flight in command-conventions.md; commands reference by link. | Accepted |
| ADR-057 | Template Extraction Pattern | Prompt blocks >100 words extracted to templates/; command retains one-line reference. | Accepted |
| ADR-058 | Inline Reviewer Replaces Async Agent | impl-reviewer: async Agent → inline Skill(); HIGH risk only; 1 auto-fix retry. | Accepted |
| ADR-059 | Light Retro ADR Gate | `<!-- adr: required -->` gates full ADR write; absent → one-line summary only. | Accepted |
| ADR-060 | Autonomous Sprint Mode | autonomous_mode=true: clarity scoring, inline reviewers, auto-fix, auto-retro; only 3 interrupt cases. | Accepted |
| — | v1.22.0 | zie-release-mode agent (fresh-context), sprint context_bundle pass-through, compact-hint two-level thresholds (80%/90%). | Accepted |
| ADR-061 | Context Efficiency Budget Table | Token budget table: hooks <500t, commands <2000t, agents <10000t; load-context once per session not per task. | Accepted |
| ADR-062 | Once-Per-Session /tmp Flag Pattern | Once-per-session behavior via scoped `/tmp/zie-{project}/` flags; hooks write flag on first fire, check on subsequent calls. | Accepted |
| ADR-063 | Effort Routing Strategy | Effort routing: low (status/single-step), medium (multi-step+brainstorm+spec-design), high (sprint only). | Accepted |
| — | v1.23.0 | Sprint A+B: compact-hint tiers, brainstorm, /rescue /health /next, code-quality-gate, sprint-reliability, adaptive-learning. | Accepted |
| — | v1.24.0 | Sprint C+D: WIP=1 guard, event field caps, reviewer-pass marker, effort routing ADR-063, parallel retro. | Accepted |
| ADR-064 | Release Command Upgraded to Sonnet/Medium | `haiku/low` → `sonnet/medium`; prevents context-limit failures post-sprint. | Accepted |
| — | v1.25.0 | All-items enforcement, approve.py upfront, make zie-implement, semver minor bias, ADR-064. | Accepted |
| ADR-066 | Non-Claude Model Compatibility | Env var model resolution + model-unavailable detection in safety_check_agent; regex fallback when subagent model unavailable. | Accepted |
| ADR-067 | Release Skill Git Ops Direct | `/release` performs git ops directly (not via `make release`); `make _publish` hook for project publish logic. | Accepted |
| — | v1.29.0 | Mega sprint: auto-learn/decide/improve (14 phases), unified-context-cache, light-retro ADR gate, WIP=1 sequential impl. | Accepted |
