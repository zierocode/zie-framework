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
| ADR-002 | markdownlint Pre-commit Gate | Run markdownlint-cli2 via pre-commit framework on all staged .md files; MD013 line length = 120. | Accepted |
| ADR-003 | Commands Are the Control Plane, Skills Are Execution | `/zie-*` commands are the exclusive pipeline stage transition control plane; skills execute within a single stage and must never auto-advance to the next. | Accepted |
| ADR-004 | Spec Approval State Tracked via Frontmatter | After spec-reviewer approves, prepend `approved: true` YAML frontmatter to spec file; `/zie-plan` filters by this flag. | Accepted |
| ADR-005 | Hybrid Release — SDLC Gates + Project-Defined Publish | Split release into SDLC layer (`/zie-release` runs gates + bumps version) and project layer (`make release` handles git ops and project-specific publishing). | Accepted |
| ADR-006 | Reviewer Context Bundles (Phase 1/2/3 Structure) | Restructure all reviewer skills into Phase 1 (load context bundle: ADRs, components, ROADMAP), Phase 2 (checklist), Phase 3 (cross-reference checks). | Accepted |
| ADR-007 | /zie-audit — research_profile as Central Intelligence Layer | Phase 1 builds a `research_profile` struct from manifests/source; all downstream audit agents and WebSearch queries are adapted from it. | Accepted |
| ADR-008 | Shared Hook Utility Module (hooks/utils.py) | Introduce `hooks/utils.py` (stdlib-only) with `parse_roadmap_now()` and `project_tmp_path()`; imported via `sys.path.insert`. | Accepted |
| ADR-009 | Hook __main__ Guard for Direct Unit Testing | Wrap all hook execution in `if __name__ == "__main__":`; extract testable functions to module scope for direct pytest import without subprocess overhead. | Accepted |
| ADR-010 | safe_write_tmp() Hard-Fails on Symlink Detection | `safe_write_tmp()` checks `path.is_symlink()` before writing; logs WARNING and returns without writing on symlink detection — never raises. | Accepted |
| ADR-011 | find_matching_test() OSError Guards at Every Filesystem Call | Apply `try/except OSError` at every individual filesystem call in `find_matching_test()`, not just the walk entry point, to stay crash-proof on pathological filesystems. | Accepted |
| ADR-012 | Tiered Model Routing — haiku / sonnet / opus per command and skill | Three-tier routing: opus+high for zie-audit, sonnet+high/medium for design/plan/impl, haiku+low for checklist/reviewer tasks; enforced by test. | Accepted |
| ADR-013 | Plugin-Bundled MCP Server for Zero-Setup Brain Integration | Ship `.claude-plugin/.mcp.json` to auto-register `zie-memory` MCP server at plugin load; degrades gracefully when env vars are absent. | Accepted |
| ADR-014 | Async impl-reviewer with Deferred-Check Polling Pattern | Spawn impl-reviewer async after each REFACTOR; poll at next task iteration start; surface issues if found; wait for all pending reviewers before final commit (max 2 iterations). | Accepted |
| ADR-015 | Hook Test Helpers Must Clear Session-Injected Env Vars | Every `run_hook()` test helper must explicitly clear all session-injected env vars (ZIE_MEMORY_ENABLED, ZIE_AUTO_TEST_DEBOUNCE_MS, etc.) before applying test-specific overrides. | Accepted |
| ADR-016 | debounce_ms=0 Means Disabled — Guard with `> 0` | Guard the entire debounce block with `if debounce_ms > 0` to prevent APFS timestamp rounding from triggering spurious suppression when debounce is disabled. | Accepted |
| ADR-017 | impl-reviewer Upgraded from haiku/low to sonnet/medium | Upgrade impl-reviewer to sonnet/medium for better code review reasoning; spec-reviewer and plan-reviewer remain on haiku. | Accepted |
| ADR-018 | utils.py as Canonical Constants and Helpers Library | `utils.py` is the single source of truth for `BLOCKS`, `WARNS`, `SDLC_STAGES`, and `normalize_command`; no inline copies permitted in hooks. | Accepted |
| ADR-019 | load_config() Parses JSON Exclusively | `load_config()` uses `json.loads()` directly; eliminates silent INI-style fallback that was dropping all config values including `safety_check_mode`. | Accepted |
| ADR-020 | Async Stop Hooks for Non-Blocking Session End | Mark `session-learn.py` and `session-cleanup.py` as `"async": true` in hooks.json; `stop-guard.py` remains synchronous to retain its blocking capability. | Accepted |
| ADR-021 | zie-audit Downgraded from Opus/5-agents to Sonnet/3-agents + Synthesis Pass | Replace 5 Opus audit agents with 3 Sonnet dimension agents + 1 Sonnet synthesis pass; reduces cost ~72% (200K → 55K tokens); WebSearch cap reduced from 25 to 15. | Accepted |
| ADR-022 | Effort Routing Strategy for Skills and Commands | Reserve `effort: high` for `spec-design` only; all other skills default to `medium` or `low`; `write-plan` corrected from high → medium. | Accepted |
| ADR-023 | SDLC Artifact Archive Strategy | Introduce `zie-framework/archive/` with backlog/specs/plans subdirs; `make archive` moves Done-lane items post-release; excluded from reviewer context bundles. | Accepted |
| ADR-024 | Git status session cache for hot-path hooks | Add `get_cached_git_status()` / `write_git_status_cache()` to utils.py; hot-path hooks consult a TTL-based /tmp cache before spawning git subprocesses. | Accepted |
| ADR-025 | ADR Auto-Summarization via /zie-retro | When `/zie-retro` counts > 30 ADR files, generate `ADR-000-summary.md` compressing oldest ADRs into a table, then delete those individual files. | Accepted |
| ADR-026 | ROADMAP Done Section Auto-Compaction | Add `compact_roadmap_done()` to utils.py; when Done entries > 20 with some older than 6 months, compact old entries into an archive summary line. | Accepted |
| ADR-027 | Coverage Gate Lowered to 43% | Lower `--fail-under` from 50 to 43 to reflect honest pytest-only measurable coverage baseline without subprocess hooks. | Accepted |
| ADR-028 | Plugin Marketplace as Decoupled Authority | Claude Code `settings.json` (extraKnownMarketplaces) is the single authority for plugin discovery; each plugin publishes independently with no cross-repo pinning. | Accepted |
| ADR-029 | Use General-Purpose Agent for Subagents in zie-retro and zie-release | Spawn general-purpose agents (no plugin type) with all context passed inline; eliminates stale-plugin-cache failures in subagent sessions. | Accepted |
| ADR-030 | Model Routing — Haiku Default with Sonnet Escalation for Judgment Steps | Haiku is the default for zie-release and impl-reviewer; judgment steps annotated with `<!-- model: sonnet -->` for per-step escalation. | Accepted |
