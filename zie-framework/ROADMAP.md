# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /zie-backlog (Next), /zie-plan (Ready), /zie-implement (Now),
> /zie-release (Done), /zie-retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->
<!-- -->

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->
- [ ] security-critical-sprint — 8 fixes: injection, coverage, protocol, deprecation
  [plan](plans/2026-03-27-security-critical-sprint.md) ✓ approved

<!-- HIGH -->

<!-- MEDIUM -->

<!-- LOW -->

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->
<!-- Audit 2026-03-26: 53 findings, score 73/100 -->

<!-- CRITICAL -->
- [ ] Prompt injection in safety_check_agent — [audit finding](backlog/security-prompt-injection.md)
- [ ] Shell injection in input-sanitizer — [audit finding](backlog/security-shell-injection.md)
- [ ] Coverage measurement broken (20% reported) — [audit finding](backlog/fix-coverage-measurement.md)

<!-- HIGH -->
- [ ] Symlink guards + atomic_write hardening — [audit finding](backlog/security-tmp-hardening.md)
- [ ] sdlc-permissions allowlist bypass — [audit finding](backlog/security-permissions-bypass.md)
- [ ] knowledge-hash --now flag broken — [audit finding](backlog/knowledge-hash-broken-flag.md)
- [ ] Test exec_module safety + bare except — [audit finding](backlog/test-exec-module-safety.md)
- [ ] Docs sync: PROJECT.md, SECURITY.md, README — [audit finding](backlog/docs-sync-and-completeness.md)
- [ ] Hook JSON protocol fix (sdlc-context + shapes) — [audit finding](backlog/hook-json-protocol-fix.md)
- [ ] utils.load_config() silent failure — [audit finding](backlog/audit-silent-config-parse-failures.md)

<!-- MEDIUM -->
- [ ] Sonnet 4.6 medium-effort adaptation — [analysis 2026-03-27](backlog/medium-effort-optimization.md)
- [ ] Token efficiency sprint — trim prompts, cache regex, lean context — [analysis 2026-03-27](backlog/token-efficiency-sprint.md)
- [ ] Parallelize audit, test gates, retro phases — [analysis 2026-03-27](backlog/parallelize-framework-ops.md)
- [ ] SDLC artifact archiving — prevent backlog/specs/plans bloat — [analysis 2026-03-27](backlog/artifact-archive-strategy.md)
- [ ] /zie-implement guard — block if no approved plan in Ready lane — [analysis 2026-03-27](backlog/implement-no-plan-guard.md)
- [ ] Unsanitized event fields in logs — [audit finding](backlog/unsanitized-event-fields.md)
- [ ] Consolidate atomic write functions — [audit finding](backlog/consolidate-utils-patterns.md)
- [ ] Dead code cleanup (audit skill, idle-log, scaffolding) — [audit finding](backlog/dead-code-cleanup.md)
- [ ] Deprecated datetime.utcnow() — [audit finding](backlog/deprecated-api-cleanup.md)
- [ ] Integration test depth (beyond "doesn't crash") — [audit finding](backlog/audit-weak-nocrash-assertions.md)
- [ ] Architecture cleanup (naming, SRP, patterns) — [audit finding](backlog/architecture-cleanup.md)
- [ ] Test quality gaps (weak assertions, edge cases) — [audit finding](backlog/test-quality-gaps.md)
- [ ] Standards compliance (SLSA, OpenSSF, CI) — [audit finding](backlog/standards-compliance.md)

<!-- LOW -->
- [ ] Path traversal restrictions — [audit finding](backlog/security-path-traversal.md)

## Later — Someday / Maybe

<!-- Good ideas, not yet prioritized. -->

<!-- (All 4 former Later items moved to Next — 2026-03-24) -->

---

## Done

<!-- Completed items. Never delete — this is history. -->

- [x] Lean & Efficient Optimization — hook consolidation (intent-sdlc.py),
  ROADMAP session cache, zie-audit 5 Opus→3 Sonnet + synthesis, effort
  right-sizing, zie-implement/zie-plan parallel cap removed, archive-plans
  Makefile target — 1491 unit + 62 integration tests — v1.10.0 2026-03-27
- [x] Security + code quality sprint — 10 features: coverage measurement fix,
  shell injection + /tmp hardening + path traversal security fixes, subprocess
  timeouts, test quality edge cases, utils consolidation (normalize_command,
  BLOCKS/WARNS, SDLC_STAGES, configurable TEST_INDICATORS), docs sync, async
  Stop hooks, hook-events JSON schema, standards compliance (log prefix audit,
  safe_project_name in notification-log) — 1513 unit + 63 integration tests
  — v1.9.0 2026-03-25
- [x] async-skills-background-execution — convert long-running skills to Agent + run_in_background,
  TaskCreate for progress tracking, TaskOutput for completion notification — v1.8.0 2026-03-24
- [x] parallel-execution-patterns — max 4 parallel tasks/Agents, file conflict detection,
  depends_on annotation syntax, documentation + unit tests — v1.8.0 2026-03-24
- [x] parallel-model-effort-optimization — model routing + context:fork + parallel execution
  in retro/implement/release, new docs-sync-check skill — v1.8.0 2026-03-24
- [x] Performance + quality sprint — 23 features: pipeline speed (inline guidance,
  lazy loading, parallel audit research, terse skills), tooling (CI/CD, pre-commit,
  semver bump gate, integration tests), workflow (velocity tracking, retro sync,
  next-item loop), bug fixes (session env var pollution in hook tests)
  — v1.7.0 2026-03-24
- [x] Deep integration sprint — 26 features: hooks for every Claude Code event,
  MCP bundle, agent isolation, session-wide agents, model routing, 1101 tests
  — v1.6.0 2026-03-24
- [x] Security + quality audit sprint — 39 security fixes, 400 tests,
  shared hook utils, Bandit SAST, Dependabot, signed releases, SLSA L1
  — v1.5.0 2026-03-24
- [x] Safety hook fix — exit(2), URL hardening, dead code removal
  — v1.4.1 2026-03-23
- [x] Hook refactor — shared utils, /tmp isolation, session-cleanup Stop hook
  — v1.4.1 2026-03-23
- [x] Test hardening — autouse fixtures, JSON assertions, find_matching_test,
  ROADMAP edge cases, debounce boundary — v1.4.1 2026-03-23
- [x] Docs + standards sprint — plugin.json sync, ADR canonicalization,
  SECURITY.md, .cz.toml, CHANGELOG translation — v1.4.1 2026-03-23
- [x] /zie-audit — 9-dimension project audit, external research via
  WebSearch/WebFetch, scored report, backlog integration — v1.4.0 2026-03-23
- [x] Pipeline fixes — implement commit step, release verify consolidation,
  Makefile --amend for plugin.json — v1.4.0 2026-03-23
- [x] Reviewer depth — context bundle (decisions/ + ROADMAP + context.md) for
  spec/plan/impl reviewers — v1.3.0 2026-03-23
- [x] Quick spec — `/zie-spec "idea"` skips backlog, inline idea → spec-design
  directly — v1.3.0 2026-03-23
- [x] Hybrid release — `make release NEW=<v>` skeleton in Makefile templates;
  `/zie-release` readiness gate + delegation; `/zie-init` negotiates skeleton —
  v1.3.0 2026-03-23
- [x] Post-release pipeline audit — 33 issues (6 critical, 16 important,
  11 minor) across all 10 commands + 10 skills + hooks; ADR-003 + ADR-004;
  README pipeline section — 2026-03-23
- [x] SDLC pipeline redesign — 6-stage pipeline (backlog→spec→plan→implement→
  release→retro) with spec/plan/impl reviewer quality gates — 2026-03-23
- [x] zie-init deep scan + knowledge drift detection — Agent(Explore) scan,
  knowledge_hash, /zie-resync command — 2026-03-23
- [x] Remove all superpowers dependencies — commands, hooks, config, docs fully
  self-contained — 2026-03-23
- [x] Knowledge Architecture — PROJECT.md hub + project/* spokes, templates,
  zie-retro sync — v1.1.0 2026-03-22
- [x] E2E Optimization — intent-driven steps, config collapse, handoff blocks —
  v1.1.0 2026-03-22
- [x] Branding & Naming Consistency — Thai-primary, renamed phases, batch
  release support — v1.1.0 2026-03-22
- [x] test-pyramid skill in /zie-build — RED phase now invokes
  Skill(zie-framework:test-pyramid) — 2026-03-22
- [x] /zie-status test health detection — .pytest_cache/lastfailed logic, mtime
  stale check — 2026-03-22
- [x] /zie-fix memory enhancement — batch recall domain+tags, root cause pattern
  format — 2026-03-22
- [x] Add unit tests for all hooks (pytest) — 53 tests across 6 hooks, fixed rm
  -rf / bug — 2026-03-22
- [x] Fork superpowers skills into zie-framework/skills/ — spec-design,
  write-plan, debug, verify — 2026-03-22
- [x] SDLC Gate Enforcement + Parallel Agents — /zie-plan, backlog-first,
  pre-flight gates, zie-memory deep integration — 2026-03-22
- [x] Initial plugin scaffolding — hooks, commands, skills, templates —
  2026-03-22
- [x] Project initialized with zie-framework — 2026-03-22

---

## Icebox — Deliberately Deferred

<!-- Good ideas explicitly put on hold. Include reason. -->

<!-- reason: needs more research / out of scope for now / dependency on X -->
