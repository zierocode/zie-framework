# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /backlog (Next), /plan (Ready), /implement (Now),
> /release (Done), /retro (reprioritization).

---

## Now — Active Sprint

- [ ] compact-output-lean — [spec](specs/2026-04-15-compact-output-lean-design.md) [plan](plans/2026-04-15-compact-output-lean.md)

---

## Ready — Approved Plans — [spec](specs/2026-04-15-intent-sdlc-lean-design.md) [plan](plans/2026-04-15-intent-sdlc-lean.md)
- [ ] compact-output-lean — [spec](specs/2026-04-15-compact-output-lean-design.md) [plan](plans/2026-04-15-compact-output-lean.md)
- [ ] cache-systems-consolidate — [spec](specs/2026-04-15-cache-systems-consolidate-design.md) [plan](plans/2026-04-15-cache-systems-consolidate.md) ← merged config-session-cache + roadmap-cache-unify
- [ ] command-conventions — [spec](specs/2026-04-15-command-conventions-design.md) [plan](plans/2026-04-15-command-conventions.md)
- [ ] command-compress-batch — [spec](specs/2026-04-15-command-compress-batch-design.md) [plan](plans/2026-04-15-command-compress-batch.md) ← merged sprint+status+retro+release
- [ ] playwright-version-cache — [spec](specs/2026-04-15-playwright-version-cache-design.md) [plan](plans/2026-04-15-playwright-version-cache.md)
- [ ] audit-error-path-coverage — [spec](specs/2026-04-15-audit-error-path-coverage-design.md) [plan](plans/2026-04-15-audit-error-path-coverage.md)
- [ ] audit-prompt-injection-hardening — [spec](specs/2026-04-15-audit-prompt-injection-hardening-design.md) [plan](plans/2026-04-15-audit-prompt-injection-hardening.md)
- [ ] audit-error-handling-cleanup — [spec](specs/2026-04-15-audit-error-handling-cleanup-design.md) [plan](plans/2026-04-15-audit-error-handling-cleanup.md)
- [ ] audit-quick-wins-batch — [spec](specs/2026-04-15-audit-quick-wins-batch-design.md) [plan](plans/2026-04-15-audit-quick-wins-batch.md) ← merged quick-wins+hardcoded-test-paths+stale-docs-refresh+test-quality-fixes+version-sync

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

<!-- -->

---

## Done — v1.30.1 (2026-04-15)

- [x] skill-manual-revise — Compress SKILL.md files 1492→1183 lines — 2026-04-15
- [x] skill-manual-auto-inject — Auto-inject skill context for active SDLC stage — 2026-04-15
- [x] init-scaffold-claude-code-config — Scaffold .claude/ settings.json, rules/sdlc.md, .ignore during /init — 2026-04-15
- [x] backlog-dedup-expand — Dedup check against Done items and expand existing items — 2026-04-15
- [x] intent-sdlc-lean — Separate new-intent patterns, raise threshold to 50, strong-intent bypass — 2026-04-15
- [x] status-roadmap-content — Show Problem excerpts and spec/plan status per Now/Ready item — 2026-04-15
- [x] py39-compat-union-type — Fix Python 3.9 compatibility: add `from __future__ import annotations` to hooks using `X | None` union syntax, fix broken import path in zie_context_loader — 2026-04-15

---

## Done — v1.30.0 (2026-04-14)

**Sprint: Context Loading + Non-Claude Compatibility**

- [x] context-loader-sprint — Auto-load zie-framework context at session start: hooks/zie_context_loader.py, session-resume.py integration, session cache with mtime-gate — 2026-04-14
- [x] context-load-smart — Deduplicate context loading: load-context skill (already exists), subagent-context content-hash cache, reviewer context_bundle passthrough, ROADMAP cache docs — 2026-04-14
- [x] agent-mode-compat — Document non-Claude limitations (model:/effort: frontmatter, --agent flag), add implement-local Makefile target, update ADR-066 — 2026-04-14

---

## Done — v1.29.0 (2026-04-14)

### Autonomous Features (NEW)
- [x] auto-learn — Pattern extraction from sessions, session memory JSON, pending_learn marker
- [x] auto-decide — Proactive suggestions on test failure/spec complete (max 3/session, 5min cooldown)
- [x] auto-improve — Auto-apply high-confidence patterns (≥0.95) to MEMORY.md at session start

### Core Efficiency
- [x] unified-context-cache — Centralize ROADMAP/ADR caching with session-scoped TTL
- [x] content-hash-ttl-increase — TTL 600s → 1800s with session-id salt
- [x] test-lookup-caching — Cache test→source mapping in .zie/cache/test-cache.json
- [x] sprint-context-passthrough — Phase bundle eliminates redundant disk reads
- [x] intent-pattern-single-pass — 65 regex checks → 1 combined regex
- [x] command-map-pre-load — Cache command map, invalidate on SKILL.md change
- [x] reviewer-context-enforcement — context_bundle required for reviewers
- [x] stop-handler-merge — Consolidated 3 Stop hooks → 1
- [x] pre-computed-version — Version computed at sprint start
- [x] combined-nudge-checks — Single git log pass for all nudge checks

<!-- -->

---

## Done

<!-- Completed items. Never delete — this is history. -->

- [x] release-makefile-conflict-fix — Fix /release skill vs make release duplication (tag already exists error), add make _publish target, deprecate make release — v1.28.4 2026-04-14
- [x] subagent-context-test-fix — Fix test flakiness from content-hash cache TTL, add clear_content_hash_cache() helper, add decisions/ADR-000-summary.md fixture — v1.28.2 2026-04-14
- [x] fix-impl-reviewer-simplify — Reconnect impl-reviewer skill to /implement (replace inline checklist), fix broken code-simplifier → simplify reference, clean orphaned agent file — v1.28.2 2026-04-14
- [x] review-loop-optimization — Fix max-iterations contradiction, unify sprint vs manual retry, remove speculative file-existence checks, pass context_bundle to avoid re-reads — v1.28.2 2026-04-14
- [x] compact-recovery — Compact verification in session-resume, sprint state enrichment (current_task + tdd_phase), PostCompact active-workflow guard, simplify compact-hint tiers — v1.28.2 2026-04-14
- [x] release-non-claude-fallback — Add non-Claude advisory to /release, make release-local target, remove inline model: comments from release.md + impl-reviewer/SKILL.md, update model-routing-v2 tests — v1.28.1 2026-04-13
- [x] GLM/Ollama Cloud Compatibility — env var model resolution + model-unavailable detection + tests + ADR-066 — v1.28.0 2026-04-13
- [x] sprint-phase2-resilience — per-item .sprint-state updates (granular resume) + /compact between Phase 2 items (overflow prevention) — v1.27.0 2026-04-13
- [x] sprint-efficiency-quality — 3 items: intent-sdlc session-level dedup cache (skip re-injection when context unchanged, file-based 600s TTL), quality-gate staged-files bandit (replace rglob[:20] with git diff --cached), implement conditional simplify step (Δ>50 triggers code-simplifier, else skipped) — v1.26.0 2026-04-13
- [x] v1.25.0-fixes — Post-sprint hotfixes: all-items enforcement in /sprint (no silent drops, consolidation rules), semver minor bias fix, approve.py upfront pattern (3 commands), Skill(zie-implement) → make zie-implement, release→sonnet/medium ADR-064 — 2535 unit tests — v1.25.0 2026-04-13
- [x] sprint-c-d — Sprint C+D (5 items): implement WIP=1 Now-lane guard, event field length caps (sanitize_log_field max_len=10240), reviewer-pass marker handshake (subagent-stop↔approve.py), effort routing ADR-063 (brainstorm+spec-design high→medium), parallel retro ops (ADR writes + ROADMAP update concurrent) — 2525 unit tests — v1.24.0 2026-04-12
- [x] sprint-a-b — Sprint A+B (10 items): framework-self-awareness (PROJECT.md staleness, playwright CVE guard, session-resume env injection), context-efficiency (3-tier compact-hint 70%/80%/90%, once-per-session flags), intent-intelligence (short-msg gate, idle-sprint gate, brainstorm patterns), brainstorming-skill (4-phase discovery + handoff.md), conversation-capture (design-tracker + stop-capture), /rescue, /health, session-continuity (.remember/now.md snippet), /next (backlog ranking), code-quality-gate (warn-only bandit/diff/coverage), sprint-reliability (.sprint-state + resume), adaptive-learning (session-learn pattern log + intent-sdlc threshold adjust) — 2501 unit tests — v1.23.0 2026-04-12
- [x] context-token-reduction-hotfix — zie-release-mode agent (fresh-context release), sprint context_bundle pass-through (plan-reviewer), compact-hint two-level thresholds (80% soft / 90% hard), ADR-000-summary.md trim to 1559w — 2345 unit tests — v1.22.0 2026-04-06
- [x] lean-autonomous-sprint — autonomy + lightweight retro: autonomous mode flag, clarity detection, interruption protocol, inline reviewers (spec/plan/impl), auto-fix protocol, light retro (ADR gate), sprint Phase 1 refactor (Skill calls not Agent), Phase 4 auto-run retro — 2345 unit tests — v1.21.0 2026-04-06
- [x] lean-efficiency-sprint-v1.20.0 — 5 items: preflight-consolidation (canonical pre-flight guard + 6-command consolidation), reviewer-context-dedup (delete dead skill + 213w cleanup), phase-prose-cleanup (200w reduction sprint/retro/release), init-scan-prompt-extract (400w prompt → template + compress step 0+7), argument-parsing-inline (Python parse blocks → argument tables in spec+sprint) — 2323 unit + 59 integration tests — v1.20.0 2026-04-04
- [x] token-efficiency-v1 — 7 tasks: ADR summary gate (ADR-000-summary.md), load-context fast-path (ADR caching), reviewer fast-paths (inline context load), retro auto-summary (ADR-000-summary.md update), CLAUDE.md cache structure (stable/dynamic sections), skill compression (12 files, 2.1% reduction), command compression (14 files, 4.7% reduction) — 2305 unit + 1 skipped tests — v1.19.1 2026-04-04
- [x] sprint10-lean-quality-refactor-v1.19.0 — 45 items: model downsizing (10 items: /hotfix, /release, /retro, impl-reviewer, resync, init, fix, plan, write-plan, debug), lean refactoring (15 items: lean-sprint-phase2, lean-retro-self-tuning, lean-prompt-pass-through, lean-auto-test-context, lean-intent-sdlc-idle-state, lean-chore-git-add, lean-knowledge-hash, lean-status-knowledge-hash, lean-subagent-context-idle, lean-implement-agent-mode, lean-verify-check2, lean-intent-sdlc-missing-tracks, lean-subagent-stop-no-matcher, lean-sec-prompt-injection-subagent, lean-mcp-zie-memory), intent detection patterns (hotfix, chore, spike), docs-sync (README sync), quality features (5 items: lean-fix-hotfix-triage, lean-spike-gitignore, lean-observability-health-command, lean-write-plan-duplicate-conflict-check, lean-plan-reviewer-n-squared, lean-notification-log-double-guard, lean-dep-pinning-inconsistency, lean-playwright-version-magic-constant), leadership tasks (3 items: lean-claudemd-trim, lean-stop-guard-nudge, lean-load-context-triple-invoke, lean-retro-git-log-quad) — 2294 unit + 1 skipped tests — v1.19.0 2026-04-04
- [x] sprint9.1-efficiency-hotspot-v1.18.1 — 5 items: consolidate reviewer disk fallback, fix release config triple read, fix retro ROADMAP redundant reads, align load-context ADR cache protocol, fix sprint ROADMAP phase rebind — 2175 unit + 59 integration tests — v1.18.1 2026-04-04
- [x] sprint9-command-refactor-v1.18 — 4 items: UX output formatting and progress visibility, workflow enforcement and escape hatches, smarter framework intelligence, remove zie- prefix from command names — 2162 unit + 59 integration tests — v1.18.0 2026-04-04
- [x] sprint8-efficiency-v1.17 — 29 items: Haiku model for safety-check agent (~80% cost cut), XML injection guard in safety-check prompt, mtime-gate ROADMAP cache (ADR-045), fire-and-forget session-resume drift check, strip static additionalContext from 3 hooks, shared load-context skill (ADR-048), shared reviewer-context skill, retro inline ADR+ROADMAP writes (ADR-047), docs-sync via Skill() in retro+release, sprint Phase 1 skill chain, subagent-context Explore guard (ADR-046), wip-checkpoint counter fix, task-gate silent exit, retro-format skill deleted, pin pytest CVE-2025-71176, zie-plan Notes removed, stop-hooks matcher documented — 2083 unit + 59 integration tests — v1.17.0 2026-04-04
- [x] sprint7-optimization-v1.17 — 12 features: merge-safety-hooks (consolidate PreToolUse), split-utils-py (5 sub-modules, 0 regressions), sprint-agent-audit (Skill not Agent in Phase 3), implement-skill-dedup (Skill pointer not prose), roadmap-done-rotation (auto-archive >90d), audit-mcp-check (MCP server audit), proactive-compact-hint (context usage warning), plus 5 earlier items (truncate-auto-test, intent-sdlc-early-exit, release-inline-gates, retro-inline-format, zie-init-delegate-scan) — 2085 unit + 59 integration tests — v1.16.3 2026-04-04
- [x] v1.16.2-maintenance — ROADMAP backlog refresh (12 Next items), pre-commit hook simplified to stub — v1.16.2 2026-04-03
- [x] audit-comprehensive-v1 — 26 fixes: hook timing instrumentation, env permissions (0o600), input guarding (braces), test improvements (6 ADR boundary cases, structural assertions), security hardening (command length cap, nosec annotation), coverage gate 43%→48%, pytest markers consolidated, dead code removed, README path fixed 2065 unit + 63 integration tests — v1.16.0 2026-04-01
- [x] zie-sprint — sprint clear command for batch pipeline (phase-parallel orchestration) — v1.15.0 2026-04-01
- [x] test-fast-fix — --lfnf=none + raw pytest fallback, make test-fast <1s after clean commit — v1.14.2 2026-03-30
- [x] pipeline-speed-v1 — make test-fast Gate 1, redundant test-run elimination, word count standardization, mapfile fix, docs-sync dedup — v1.14.1 2026-03-30
- [x] sprint7-maximum-agentism — agentic-pipeline-v2, context-lean-sprint, parallel-release-gates, model-routing-v2, workflow-lean, dx-polish — 1908 unit + 63 integration tests — v1.14.0 2026-03-30
- [x] sprint6-audit-v2-portability — zie-audit v2 (7 dimensions + external research), 5 portability fixes (agents, safety hook, markdownlint, venv python, dev branch), plugin marketplace decoupling — v1.13.0 2026-03-30
- [x] sprint5-pipeline-quality — 13 features: pipeline-gate-enforcement, adr-session-cache, adr-auto-summarization, user-onboarding-sdlc, retro-release-lean-context, hook-resilience-tests, test-suite-tiering, roadmap-done-compaction, hook-config-hardening, dry-utils-cleanup, zie-init-single-scan, archive-ttl-rotation, coverage-make-clean — 1784 unit + 63 integration tests — v1.12.0 2026-03-30
- [x] sprint4-final-clearance — git status caching (hot path), stronger test assertions (5 files), safety_check_mode documented in CLAUDE.md — 1566 unit + 62 integration tests — v1.11.1 2026-03-29
- [x] sprint3-framework-optimization — token trim (implement/release/retro), parallel ADR+ROADMAP agents in retro, context bundle for plan-reviewer, effort routing (write-plan high→medium, ADR-022), CI hardening (make test→test-unit), parse_roadmap_ready(), 12 new test files — 1555 unit tests — v1.11.0 2026-03-27
- [x] sprint2-hardening-quality — /tmp write permissions (0o600), sdlc-permissions metachar guard (;&&||`$()), exec_module replacement (SourceFileLoader), idle_prompt dead code removal, utils helpers (is_zie_initialized, get_project_name), notification-log cleanup — 1528 unit tests — v1.11.0 2026-03-27
- [x] security-critical-sprint — 8 fixes: prompt injection (safety_check_agent), shell injection (input-sanitizer), coverage gate documentation + smoke target, knowledge-hash --now flag, load_config() stderr visibility, JSON protocol (sdlc-compact + auto-test), datetime.utcnow() deprecation (subagent-stop), log field sanitization (stopfailure-log + notification-log) — 1518 unit + 62 integration tests — v1.10.1 2026-03-27
- [x] Lean & Efficient Optimization — hook consolidation (intent-sdlc.py), ROADMAP session cache, zie-audit 5 Opus→3 Sonnet + synthesis, effort right-sizing, zie-implement/plan parallel cap removed, archive-plans Makefile target — 1491 unit + 62 integration tests — v1.10.0 2026-03-27
- [x] Security + code quality sprint — 10 features: coverage measurement fix, shell injection + /tmp hardening + path traversal security fixes, subprocess timeouts, test quality edge cases, utils consolidation (normalize_command, BLOCKS/WARNS, SDLC_STAGES, configurable TEST_INDICATORS), docs sync, async Stop hooks, hook-events JSON schema, standards compliance (log prefix audit, safe_project_name in notification-log) — 1513 unit + 63 integration tests — v1.9.0 2026-03-25
- [x] async-skills-background-execution — convert long-running skills to Agent + run_in_background, TaskCreate for progress tracking, TaskOutput for completion notification — v1.8.0 2026-03-24
- [x] parallel-execution-patterns — max 4 parallel tasks/Agents, file conflict detection, depends_on annotation syntax, documentation + unit tests — v1.8.0 2026-03-24
- [x] parallel-model-effort-optimization — model routing + context:fork + parallel execution in retro/implement/release, new docs-sync-check skill — v1.8.0 2026-03-24
- [x] Performance + quality sprint — 23 features: pipeline speed (inline guidance, lazy loading, parallel audit research, terse skills), tooling (CI/CD, pre-commit, semver bump gate, integration tests), workflow (velocity tracking, retro sync, next-item loop), bug fixes (session env var pollution in hook tests) — v1.7.0 2026-03-24
- [x] Deep integration sprint — 26 features: hooks for every Claude Code event, MCP bundle, agent isolation, session-wide agents, model routing, 1101 tests — v1.6.0 2026-03-24
- [x] Security + quality audit sprint — 39 security fixes, 400 tests, shared hook utils, Bandit SAST, Dependabot, signed releases, SLSA L1 — v1.5.0 2026-03-24
- [x] Safety hook fix — exit(2), URL hardening, dead code removal — v1.4.1 2026-03-23
- [x] Hook refactor — shared utils, /tmp isolation, session-cleanup Stop hook — v1.4.1 2026-03-23
- [x] Test hardening — autouse fixtures, JSON assertions, find_matching_test, ROADMAP edge cases, debounce boundary — v1.4.1 2026-03-23
- [x] Docs + standards sprint — plugin.json sync, ADR canonicalization, SECURITY.md, .cz.toml, CHANGELOG translation — v1.4.1 2026-03-23
- [x] /audit — 9-dimension project audit, external research via WebSearch/WebFetch, scored report, backlog integration — v1.4.0 2026-03-23
- [x] Pipeline fixes — implement commit step, release verify consolidation, Makefile --amend for plugin.json — v1.4.0 2026-03-23
- [x] Reviewer depth — context bundle (decisions/ + ROADMAP + context.md) for spec/plan/impl reviewers — v1.3.0 2026-03-23
- [x] Quick spec — `/spec "idea"` skips backlog, inline idea → spec-design directly — v1.3.0 2026-03-23
- [x] Hybrid release — `make release NEW=<v>` skeleton in Makefile templates; `/release` readiness gate + delegation; `/init` negotiates skeleton — v1.3.0 2026-03-23
- [x] Post-release pipeline audit — 33 issues (6 critical, 16 important, 11 minor) across all 10 commands + 10 skills + hooks; ADR-003 + ADR-004; README pipeline section — 2026-03-23
- [x] SDLC pipeline redesign — 6-stage pipeline (backlog→spec→plan→implement→release→retro) with spec/plan/impl reviewer quality gates — 2026-03-23
- [x] zie-init deep scan + knowledge drift detection — Agent(Explore) scan, knowledge_hash, /resync command — 2026-03-23
- [x] Remove all superpowers dependencies — commands, hooks, config, docs fully self-contained — 2026-03-23
- [x] Knowledge Architecture — PROJECT.md hub + project/* spokes, templates, zie-retro sync — v1.1.0 2026-03-22
- [x] E2E Optimization — intent-driven steps, config collapse, handoff blocks — v1.1.0 2026-03-22
- [x] Branding & Naming Consistency — Thai-primary, renamed phases, batch release support — v1.1.0 2026-03-22
- [x] test-pyramid skill in /zie-build — RED phase now invokes Skill(zie-framework:test-pyramid) — 2026-03-22
- [x] /status test health detection — .pytest_cache/lastfailed logic, mtime stale check — 2026-03-22
- [x] /fix memory enhancement — batch recall domain+tags, root cause pattern format — 2026-03-22
- [x] Add unit tests for all hooks (pytest) — 53 tests across 6 hooks, fixed rm -rf / bug — 2026-03-22
- [x] Fork superpowers skills into zie-framework/skills/ — spec-design, write-plan, debug, verify — 2026-03-22
- [x] SDLC Gate Enforcement + Parallel Agents — /plan, backlog-first, pre-flight gates, zie-memory deep integration — 2026-03-22
- [x] Initial plugin scaffolding — hooks, commands, skills, templates — 2026-03-22
- [x] Project initialized with zie-framework — 2026-03-22

---

## Icebox — Deliberately Deferred

<!-- Good ideas explicitly put on hold. Include reason. -->

<!-- reason: needs more research / out of scope for now / dependency on X -->
