# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /backlog (Next), /plan (Ready), /implement (Now),
> /release (Done), /retro (reprioritization).

---

## Now — Active Sprint

<!-- -->

---

## Ready — Approved Plans

<!-- Items with approved spec + plan, awaiting implementation. -->

---

## Next — Prioritized Backlog

<!-- Items awaiting spec. Ordered by priority. -->
- [ ] Remove GitHub CI — [backlog](backlog/remove-github-ci.md)
- [ ] Optimize Review Loop Token Waste — [backlog](backlog/optimize-review-loop-token-waste.md)

---

## Done — v1.31.0 (2026-04-15)

- [x] command-compress-batch — Compress sprint, status, retro, release commands
- [x] playwright-version-cache — Cache playwright version, skip redundant subprocess
- [x] audit-error-path-coverage — Error-path unit tests for all hooks (ADR-003)
- [x] audit-prompt-injection-hardening — BLOCK on ambiguous, XML entity escaping
- [x] audit-error-handling-cleanup — log_error helper, narrow exception types
- [x] audit-quick-wins-batch — Hardcoded paths, version sync, stale docs, test moves

## Done — v1.30.1 (2026-04-15)

- [x] cache-systems-consolidate — Unified CacheManager with mtime + session invalidation
- [x] compact-output-lean — [zf] prefix, inline hook output
- [x] skill-manual-revise — Compress SKILL.md 1492→1183 lines
- [x] skill-manual-auto-inject — Auto-inject skill context for active SDLC stage
- [x] init-scaffold-claude-code-config — Scaffold .claude/ config during /init
- [x] backlog-dedup-expand — Dedup across all ROADMAP lanes + expand option
- [x] intent-sdlc-lean — Separate new-intent patterns, raise threshold to 50
- [x] status-roadmap-content — Show Problem excerpts + spec/plan status per item
- [x] py39-compat-union-type — Fix `X | None` syntax for Python 3.9

## Done — v1.30.0 (2026-04-14) — Context Loading + Non-Claude Compat

- [x] context-loader-sprint — Auto-load context at session start, mtime-gate cache
- [x] context-load-smart — Deduplicate context loading across skills
- [x] agent-mode-compat — Document non-Claude limitations, ADR-066

## Done — v1.29.0 (2026-04-14) — Autonomous Features + Efficiency

- [x] auto-learn / auto-decide / auto-improve — Pattern extraction, suggestions, auto-apply
- [x] unified-context-cache / content-hash-ttl-increase / test-lookup-caching — Caching
- [x] sprint-context-passthrough / intent-pattern-single-pass / command-map-pre-load — Performance
- [x] reviewer-context-enforcement / stop-handler-merge / pre-computed-version / combined-nudge-checks — Cleanup

## Done — v1.28.0–v1.28.4 (2026-04-13–14) — Resilience + Compat

- [x] release-makefile-conflict-fix — v1.28.4
- [x] subagent-context-test-fix / fix-impl-reviewer-simplify / review-loop-optimization / compact-recovery — v1.28.2
- [x] release-non-claude-fallback — v1.28.1
- [x] GLM/Ollama Cloud Compatibility — v1.28.0

## Done — v1.27.0 (2026-04-13) — Sprint Resilience

- [x] sprint-phase2-resilience — per-item state + /compact between items

## Done — v1.26.0 (2026-04-13) — Efficiency + Quality

- [x] sprint-efficiency-quality — dedup cache, bandit gate, conditional simplify

## Done — v1.25.0 (2026-04-13) — Post-Sprint Fixes

- [x] v1.25.0-fixes — all-items enforcement, semver bias, approve.py pattern

## Done — v1.24.0 (2026-04-12) — Sprint C+D

- [x] sprint-c-d — WIP=1 guard, field caps, reviewer handshake, effort routing ADR-063

## Done — v1.23.0 (2026-04-12) — Sprint A+B

- [x] sprint-a-b — 10 items: self-awareness, context-efficiency, intent-intelligence, brainstorming, conversation-capture, /rescue, /health, /next, quality-gate, adaptive-learning

## Done — v1.22.0 (2026-04-06) — Token Reduction

- [x] context-token-reduction-hotfix — release-mode agent, compact-hint thresholds

## Done — v1.21.0 (2026-04-06) — Autonomous Sprint

- [x] lean-autonomous-sprint — autonomous mode, clarity detection, interruption protocol, inline reviewers, light retro

## Done — v1.20.0 (2026-04-04) — Lean Efficiency

- [x] lean-efficiency-sprint — 5 items: preflight-consolidation, reviewer-context-dedup, phase-prose-cleanup, init-scan-prompt-extract, argument-parsing-inline

## Done — v1.19.0–v1.19.1 (2026-04-04) — Token Efficiency + Quality

- [x] token-efficiency-v1 — 7 tasks: ADR summary, load-context fast-path, reviewer fast-paths, retro auto-summary, CLAUDE.md cache, skill/command compression — v1.19.1
- [x] sprint10-lean-quality-refactor — 45 items: model downsizing, lean refactoring, intent patterns, docs-sync, quality features — v1.19.0

## Done — v1.18.0–v1.18.1 (2026-04-04) — Command Refactor + Efficiency

- [x] sprint9.1-efficiency-hotspot — 5 items: reviewer fallback, release config, retro reads, ADR cache, sprint rebind — v1.18.1
- [x] sprint9-command-refactor — 4 items: UX formatting, workflow enforcement, framework intelligence, zie- prefix removal — v1.18.0

## Done — v1.17.0 (2026-04-04) — Efficiency Sprint

- [x] sprint8-efficiency — 29 items: Haiku safety, XML guard, mtime-gate ROADMAP, load-context skill, retro inline, subagent-context guard
- [x] sprint7-optimization — 12 features: safety-hooks merge, split-utils-py, sprint-agent-audit, roadmap-done-rotation, audit-mcp-check, compact-hint

## Done — v1.16.0–v1.16.3 (2026-04-01–04) — Audit + Maintenance

- [x] v1.16.2-maintenance — ROADMAP backlog refresh, pre-commit stub
- [x] audit-comprehensive-v1 — 26 fixes: timing, permissions, security, coverage 43→48% — v1.16.0

## Done — v1.15.0 (2026-04-01) — Sprint Command

- [x] zie-sprint — Batch pipeline command

## Done — v1.14.0–v1.14.2 (2026-03-30) — Pipeline Speed

- [x] test-fast-fix / pipeline-speed-v1 — v1.14.1–v1.14.2
- [x] sprint7-maximum-agentism — agentic-pipeline-v2, parallel gates, model routing — v1.14.0

## Done — v1.13.0 (2026-03-30) — Audit v2 + Portability

- [x] sprint6-audit-v2-portability — zie-audit v2, 5 portability fixes

## Done — v1.12.0 (2026-03-30) — Pipeline Quality

- [x] sprint5-pipeline-quality — 13 features: gate enforcement, ADR cache, test tiering, archive rotation

## Done — v1.11.0–v1.11.1 (2026-03-27–29) — Framework Optimization

- [x] sprint4-final-clearance — git caching, assertions — v1.11.1
- [x] sprint3-framework-optimization — token trim, parallel retro, effort routing — v1.11.0
- [x] sprint2-hardening-quality — permissions, metachar guard, utils — v1.11.0

## Done — v1.10.0–v1.10.1 (2026-03-27) — Security + Lean

- [x] security-critical-sprint — 8 fixes: prompt/shell injection, JSON protocol, datetime deprecation — v1.10.1
- [x] Lean & Efficient Optimization — hook consolidation, ROADMAP cache, audit synthesis — v1.10.0

## Done — v1.9.0 (2026-03-25) — Security + Quality

- [x] Security + code quality sprint — 10 features: injection fixes, subprocess timeouts, utils consolidation, hook-events schema

## Done — v1.8.0 (2026-03-24) — Parallel + Async

- [x] async-skills-background-execution / parallel-execution-patterns / parallel-model-effort-optimization

## Done — v1.7.0 (2026-03-24) — Performance + Quality

- [x] Performance + quality sprint — 23 features: pipeline speed, CI/CD, workflow

## Done — v1.6.0 (2026-03-24) — Deep Integration

- [x] Deep integration sprint — 26 features: all hooks, MCP, agents, model routing

## Done — v1.5.0 (2026-03-24) — Security Audit

- [x] Security + quality audit sprint — 39 fixes, 400 tests, Bandit, SLSA L1

## Done — v1.4.0–v1.4.1 (2026-03-23) — Security + Standards

- [x] Safety hook fix / Hook refactor / Test hardening / Docs + standards — v1.4.1
- [x] /audit / Pipeline fixes — v1.4.0

## Done — v1.3.0 (2026-03-23) — Reviewers + Release

- [x] Reviewer depth / Quick spec / Hybrid release / Post-release audit / SDLC pipeline redesign / zie-init deep scan / Remove superpowers dependencies

## Done — v1.1.0–v1.2.0 (2026-03-22) — Architecture + Branding

- [x] Knowledge Architecture / E2E Optimization / Branding & Naming / test-pyramid / /status / /fix / Unit tests / Fork skills / SDLC Gate Enforcement

## Done — v1.0.0 (2026-03-22) — Initial

- [x] Initial plugin scaffolding — hooks, commands, skills, templates
- [x] Project initialized with zie-framework

---

## Icebox — Deliberately Deferred

<!-- Good ideas explicitly put on hold. Include reason. -->

<!-- reason: needs more research / out of scope for now / dependency on X -->