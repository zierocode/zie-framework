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
| ADR-001 | Reviewer Skills as Dispatched Subagents | Dispatch spec/plan/impl reviewers as fresh subagents with isolated context and a binary verdict checklist; cap at 3 iterations. | Accepted |
| ADR-002 | markdownlint Pre-commit Gate | Run markdownlint-cli2 via pre-commit on all staged .md files; MD013 line length = 120. | Accepted |
| ADR-003 | Commands Are the Control Plane, Skills Are Execution | Commands are the exclusive pipeline stage transition control plane; skills execute within a single stage and must never auto-advance. | Accepted |
| ADR-004 | Spec Approval State Tracked via Frontmatter | After spec-reviewer approves, prepend `approved: true` YAML frontmatter to spec file; `/plan` filters by this flag. | Accepted |
| ADR-005 | Hybrid Release — SDLC Gates + Project-Defined Publish | Split release into SDLC layer (gates + version bump) and project layer (git ops + publishing). | Accepted |
| ADR-006 | Reviewer Context Bundles | Phase 1: load context bundle (ADRs, ROADMAP). Phase 2: checklist. Phase 3: cross-reference checks. | Accepted |
| ADR-007 | research_profile as Audit Intel Layer | Phase 1 builds research_profile from manifests; all audit agents and WebSearch queries adapt from it. | Accepted |
| ADR-008 | Shared Hook Utility Module (hooks/utils.py) | Introduce `hooks/utils.py` (stdlib-only) with `parse_roadmap_now()` and `project_tmp_path()`; imported via `sys.path.insert`. | Accepted |
| ADR-009 | Hook __main__ Guard for Direct Unit Testing | Wrap hook execution in `if __name__ == "__main__":`; extract testable functions to module scope for direct pytest import. | Accepted |
| ADR-010 | safe_write_tmp() Hard-Fails on Symlink Detection | `safe_write_tmp()` checks `path.is_symlink()` before writing; logs WARNING and returns without writing — never raises. | Accepted |
| ADR-011 | find_matching_test() OSError Guards at Every Filesystem Call | Apply `try/except OSError` at every individual filesystem call in `find_matching_test()` to stay crash-proof. | Accepted |
| ADR-012 | Tiered Model Routing — haiku / sonnet / opus | Three-tier routing: opus+high for zie-audit, sonnet+high/medium for design/plan/impl, haiku+low for checklist/reviewer tasks. | Accepted |
| ADR-013 | Plugin-Bundled MCP Server for Zero-Setup Brain Integration | Ship `.claude-plugin/.mcp.json` to auto-register `zie-memory` MCP; degrades gracefully when env vars are absent. | Accepted |
| ADR-014 | Async impl-reviewer Deferred-Check Polling | Spawn impl-reviewer async after REFACTOR; poll at next iteration; surface issues; max 2 iterations. | Accepted |
| ADR-015 | Hook Test Helpers Must Clear Session-Injected Env Vars | Every `run_hook()` test helper must explicitly clear all session-injected env vars before applying test-specific overrides. | Accepted |
| ADR-016 | debounce_ms=0 Means Disabled — Guard with `> 0` | Guard debounce block with `if debounce_ms > 0` to prevent APFS timestamp rounding from triggering spurious suppression. | Accepted |
| ADR-017 | impl-reviewer Upgraded from haiku/low to sonnet/medium | Upgrade impl-reviewer to sonnet/medium for better reasoning; spec-reviewer and plan-reviewer remain on haiku. | Accepted |
| ADR-018 | utils.py as Canonical Constants and Helpers Library | `utils.py` is the single source of truth for `BLOCKS`, `WARNS`, `SDLC_STAGES`, and `normalize_command`. | Accepted |
| ADR-019 | load_config() Parses JSON Exclusively | `load_config()` uses `json.loads()` directly; eliminates silent INI-style fallback that was dropping config values. | Accepted |
| ADR-020 | Async Stop Hooks for Non-Blocking Session End | `session-learn.py` and `session-cleanup.py` marked `"async": true`; `stop-guard.py` remains synchronous. | Accepted |
| ADR-021 | zie-audit Cost Optimization | Replace 5 Opus agents with 3 Sonnet agents + synthesis; ~72% cost reduction; WebSearch 25 → 15. | Accepted |
| ADR-022 | Effort Routing Strategy for Skills and Commands | Reserve `effort: high` for `spec-design` only; all other skills default to `medium` or `low`; `write-plan` corrected from high → medium. | Accepted |
| ADR-023 | SDLC Artifact Archive Strategy | Introduce `zie-framework/archive/` with backlog/specs/plans subdirs; `make archive` moves Done-lane items post-release; excluded from reviewer context bundles. | Accepted |
| ADR-024 | Git Status Session Cache | Hot-path hooks consult /tmp cache before git subprocesses. | Accepted |
| ADR-025 | ADR Auto-Summarization via /zie-retro | When `/zie-retro` counts > 30 ADR files, generate `ADR-000-summary.md` compressing oldest ADRs into a table, then delete those individual files. | Accepted |
| ADR-026 | ROADMAP Done Section Auto-Compaction | Add `compact_roadmap_done()` to utils.py; when Done entries > 20 with some older than 6 months, compact old entries into an archive summary line. | Accepted |
| ADR-027 | Coverage Gate Lowered to 43% | Lower `--fail-under` from 50 to 43 to reflect honest pytest-only measurable coverage baseline without subprocess hooks. | Accepted |
| ADR-028 | Plugin Marketplace as Decoupled Authority | Claude Code `settings.json` (extraKnownMarketplaces) is the single authority for plugin discovery; each plugin publishes independently with no cross-repo pinning. | Accepted |
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
| ADR-056 | Pre-flight Guard Centralization | Canonical 3-step pre-flight extracted to command-conventions.md; 6 commands reference it by link instead of duplicating inline. | Accepted |
| ADR-057 | Template Extraction Pattern | Large inline prompt blocks (>100 words) extracted to templates/ files; command retains one-line reference. | Accepted |
| ADR-058 | Inline Reviewer Replaces Async Agent | impl-reviewer moved from async Agent spawn + polling to inline Skill(); gated on HIGH risk; auto-fix 1 retry then interrupt. | Accepted |
| ADR-059 | Light Retro ADR Gate | Full ADR writing gated on `<!-- adr: required -->` in plan; absent → one-line summary only; ~80% retro overhead reduction. | Accepted |
| ADR-060 | Autonomous Sprint Mode | autonomous_mode=true: clarity scoring, inline reviewers, auto-fix, auto-retro; only 3 interrupt cases. | Accepted |
