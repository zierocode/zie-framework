# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /backlog (Next), /plan (Ready), /implement (Now),
> /release (Done), /retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->

- [x] lean-claudemd-trim-to-trigger-table — cut CLAUDE.md to <80 lines; move hook conventions to project docs
- [x] lean-stop-guard-nudge-per-stop — session-gate git log subprocess in stop-guard; shlex.quote(slug)
- [x] lean-load-context-triple-invoke — pass context_bundle down sprint→implement chain; eliminate triple load-context call

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->
<!-- Sprint10 Phase 1 complete: 45 items spec+plan approved 2026-04-04 -->

<!-- CRITICAL -->

<!-- HIGH -->
- [x] lean-retro-git-log-quad-read — deduplicate 4 git log reads in retro.md → 1
- [ ] lean-project-md-commands-stale — sync PROJECT.md + CLAUDE.md commands/skills tables (4 missing commands, 1 ghost + 2 missing skills)
- [ ] lean-docs-sync-blind-to-project-md — extend docs-sync-check scope to verify PROJECT.md
- [ ] lean-spec-design-agent-syntax — fix @agent-spec-reviewer → Skill() in spec-design (reliability gap)
- [ ] lean-double-pretooluse-on-bash — merge safety_check_agent.py into safety-check.py (eliminate per-Bash config read)
- [ ] sec-shell-injection-confirm-wrap — add > < | \n to confirm-wrapper guard in safety-check.py:141
- [ ] sec-shell-injection-stop-guard-slug — shlex.quote(slug) in stop-guard.py:64 subprocess call
- [ ] lean-dual-audit-pipeline — collapse /audit command + zie-audit skill into one canonical pipeline [Strategic]
- [ ] lean-reviewer-context-chain-depth — reduce reviewer skill chain depth 3–4 hops → 1–2 [Strategic]

<!-- MEDIUM -->
- [x] lean-hotfix-model-overkill — /hotfix opus+high → sonnet+low (5-step mechanical track)
- [x] model-release-effort-medium-to-low — /release haiku+medium → haiku+low
- [x] model-retro-effort-medium-to-low — /retro sonnet+medium → sonnet+low
- [x] model-impl-reviewer-effort-medium-to-low — impl-reviewer haiku+medium → haiku+low
- [x] model-resync-sonnet-to-haiku — /resync sonnet+medium → haiku+medium
- [x] model-init-sonnet-to-haiku — /init sonnet+medium → haiku+medium
- [x] model-fix-effort-medium-to-low — /fix sonnet+medium → sonnet+low
- [x] model-plan-effort-medium-to-low — /plan sonnet+medium → sonnet+low
- [x] model-write-plan-effort-medium-to-low — write-plan skill sonnet+medium → sonnet+low
- [x] model-debug-effort-medium-to-low — debug skill sonnet+medium → sonnet+low
- [ ] lean-sprint-phase2-redundant — remove sprint Phase 2 (error-recovery-only masquerading as normal phase)
- [ ] lean-retro-self-tuning-blocks-release — move self-tuning proposals to non-blocking advisory at retro end
- [ ] lean-prompt-pass-through — suppress intent-sdlc injection for slash commands (extend early-exit to any /command)
- [ ] lean-auto-test-context-before-debounce — move additionalContext emit to after debounce + test-file check
- [ ] lean-intent-sdlc-idle-state-suffix — suppress task:none|stage:idle suffix when idle + unambiguous intent
- [ ] lean-chore-git-add-A — replace git add -A with targeted git add in /chore (CLAUDE.md hard rule violation)
- [ ] lean-knowledge-hash-in-implement — remove knowledge-hash bang injection from /implement banner
- [ ] lean-status-knowledge-hash-twice — deduplicate knowledge-hash computation in /status (runs twice)
- [ ] lean-subagent-context-idle-overhead — early-exit when no active task; split Explore/Plan matchers
- [ ] lean-implement-agent-mode-check — simplify /implement agent-mode gate to non-blocking advisory
- [ ] lean-verify-check2-reruns-tests — add test_output guard to verify check 2 (matches check 1 pattern)
- [ ] lean-intent-sdlc-missing-tracks — add /hotfix, /chore, /spike intent patterns to intent-sdlc.py
- [ ] lean-subagent-stop-no-matcher — investigate SubagentStop matcher support; add if possible
- [ ] lean-sec-prompt-injection-subagent — strengthen XML tag escaping in safety_check_agent.py
- [ ] lean-mcp-zie-memory-unconfigured — add zie-memory availability check before brain calls in commands

<!-- LOW -->
- [ ] lean-fix-hotfix-triage-rule — add single-sentence triage rule to /fix and /hotfix descriptions
- [ ] lean-spike-gitignore — add .gitignore guidance for spike-*/ directories in /spike
- [ ] lean-observability-health-command — add Framework Health section to /status output
- [ ] lean-write-plan-duplicate-conflict-check — remove duplicate file conflict check prose in write-plan
- [ ] lean-plan-reviewer-n-squared — replace N² pair check with O(N) file-map heuristic in plan-reviewer
- [ ] lean-notification-log-double-guard — remove redundant type guard in notification-log.py
- [ ] lean-dep-pinning-inconsistency — standardize version pinning strategy in requirements-dev.txt
- [ ] lean-playwright-version-magic-constant — document PLAYWRIGHT_MIN_VERSION derivation (CVE reference)

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

---

## Done

<!-- Completed items. Never delete — this is history. -->

- [x] sprint9.1-efficiency-hotspot-v1.18.1 — 5 items: consolidate reviewer disk fallback, fix release config triple read, fix retro ROADMAP redundant reads, align load-context ADR cache protocol, fix sprint ROADMAP phase rebind — 2175 unit + 59 integration tests — v1.18.1 2026-04-04

- [x] sprint9-command-refactor-v1.18 — 4 items: UX output formatting and progress visibility, workflow enforcement and escape hatches, smarter framework intelligence, remove zie- prefix from command names — 2162 unit + 59 integration tests — v1.18.0 2026-04-04

- [x] sprint8-efficiency-v1.17 — 29 items: Haiku model for safety-check agent (~80% cost cut), XML injection guard in safety-check prompt, mtime-gate ROADMAP cache (ADR-045), fire-and-forget session-resume drift check, strip static additionalContext from 3 hooks, shared load-context skill (ADR-048), shared reviewer-context skill, retro inline ADR+ROADMAP writes (ADR-047), docs-sync via Skill() in retro+release, sprint Phase 1 skill chain, subagent-context Explore guard (ADR-046), wip-checkpoint counter fix, task-gate silent exit, retro-format skill deleted, pin pytest CVE-2025-71176, zie-plan Notes removed, stop-hooks matcher documented — 2083 unit + 59 integration tests — v1.17.0 2026-04-04

- [x] sprint7-optimization-v1.17 — 12 features: merge-safety-hooks (consolidate PreToolUse), split-utils-py (5 sub-modules, 0 regressions), sprint-agent-audit (Skill not Agent in Phase 3), implement-skill-dedup (Skill pointer not prose), roadmap-done-rotation (auto-archive >90d), audit-mcp-check (MCP server audit), proactive-compact-hint (context usage warning), plus 5 earlier items (truncate-auto-test, intent-sdlc-early-exit, release-inline-gates, retro-inline-format, zie-init-delegate-scan) — 2085 unit + 59 integration tests — v1.16.3 2026-04-04

- [x] v1.16.2-maintenance — ROADMAP backlog refresh (12 Next items), pre-commit hook simplified to stub — v1.16.2 2026-04-03

- [x] audit-comprehensive-v1 — 26 fixes:
  hook timing instrumentation, env permissions (0o600), input guarding (braces),
  test improvements (6 ADR boundary cases, structural assertions), security
  hardening (command length cap, nosec annotation), coverage gate 43%→48%,
  pytest markers consolidated, dead code removed, README path fixed
  2065 unit + 63 integration tests — v1.16.0 2026-04-01

- [x] zie-sprint — sprint clear command for batch pipeline (phase-parallel orchestration) — v1.15.0 2026-04-01

- [x] test-fast-fix — --lfnf=none + raw pytest fallback, make test-fast <1s after clean commit — v1.14.2 2026-03-30

- [x] pipeline-speed-v1 — make test-fast Gate 1, redundant test-run elimination, word count standardization, mapfile fix, docs-sync dedup — v1.14.1 2026-03-30

- [x] sprint7-maximum-agentism — agentic-pipeline-v2, context-lean-sprint, parallel-release-gates, model-routing-v2, workflow-lean, dx-polish — 1908 unit + 63 integration tests — v1.14.0 2026-03-30

- [x] sprint6-audit-v2-portability — zie-audit v2 (7 dimensions + external research), 5 portability fixes (agents, safety hook, markdownlint, venv python, dev branch), plugin marketplace decoupling — v1.13.0 2026-03-30

- [x] sprint5-pipeline-quality — 13 features: pipeline-gate-enforcement, adr-session-cache,
  adr-auto-summarization, user-onboarding-sdlc, retro-release-lean-context, hook-resilience-tests,
  test-suite-tiering, roadmap-done-compaction, hook-config-hardening, dry-utils-cleanup,
  zie-init-single-scan, archive-ttl-rotation, coverage-make-clean — 1784 unit + 63 integration
  tests — v1.12.0 2026-03-30

- [x] sprint4-final-clearance — git status caching (hot path), stronger test assertions (5 files),
  safety_check_mode documented in CLAUDE.md — 1566 unit + 62 integration tests — v1.11.1 2026-03-29
- [x] sprint3-framework-optimization — token trim (implement/release/retro), parallel ADR+ROADMAP
  agents in retro, archive strategy (make archive + zie-framework/archive/), implement pre-flight
  guard, effort routing (write-plan high→medium, ADR-022), CI hardening (make test→test-unit),
  parse_roadmap_ready(), 12 new test files — 1555 unit tests — v1.11.0 2026-03-27
- [x] sprint2-hardening-quality — /tmp write permissions (0o600), sdlc-permissions metachar
  guard (;&&||`$()), exec_module replacement (SourceFileLoader), idle_prompt dead code removal,
  utils helpers (is_zie_initialized, get_project_name), notification-log cleanup — 1528 unit
  tests — v1.11.0 2026-03-27
- [x] security-critical-sprint — 8 fixes: prompt injection (safety_check_agent), shell injection
  (input-sanitizer), coverage gate documentation + smoke target, knowledge-hash --now flag,
  load_config() stderr visibility, JSON protocol (sdlc-compact + auto-test), datetime.utcnow()
  deprecation (subagent-stop), log field sanitization (stopfailure-log + notification-log)
  — 1518 unit + 62 integration tests — v1.10.1 2026-03-27
- [x] Lean & Efficient Optimization — hook consolidation (intent-sdlc.py),
  ROADMAP session cache, zie-audit 5 Opus→3 Sonnet + synthesis, effort
  right-sizing, zie-implement/plan parallel cap removed, archive-plans
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
- [x] /audit — 9-dimension project audit, external research via
  WebSearch/WebFetch, scored report, backlog integration — v1.4.0 2026-03-23
- [x] Pipeline fixes — implement commit step, release verify consolidation,
  Makefile --amend for plugin.json — v1.4.0 2026-03-23
- [x] Reviewer depth — context bundle (decisions/ + ROADMAP + context.md) for
  spec/plan/impl reviewers — v1.3.0 2026-03-23
- [x] Quick spec — `/spec "idea"` skips backlog, inline idea → spec-design
  directly — v1.3.0 2026-03-23
- [x] Hybrid release — `make release NEW=<v>` skeleton in Makefile templates;
  `/release` readiness gate + delegation; `/init` negotiates skeleton —
  v1.3.0 2026-03-23
- [x] Post-release pipeline audit — 33 issues (6 critical, 16 important,
  11 minor) across all 10 commands + 10 skills + hooks; ADR-003 + ADR-004;
  README pipeline section — 2026-03-23
- [x] SDLC pipeline redesign — 6-stage pipeline (backlog→spec→plan→implement→
  release→retro) with spec/plan/impl reviewer quality gates — 2026-03-23
- [x] zie-init deep scan + knowledge drift detection — Agent(Explore) scan,
  knowledge_hash, /resync command — 2026-03-23
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
- [x] /status test health detection — .pytest_cache/lastfailed logic, mtime
  stale check — 2026-03-22
- [x] /fix memory enhancement — batch recall domain+tags, root cause pattern
  format — 2026-03-22
- [x] Add unit tests for all hooks (pytest) — 53 tests across 6 hooks, fixed rm
  -rf / bug — 2026-03-22
- [x] Fork superpowers skills into zie-framework/skills/ — spec-design,
  write-plan, debug, verify — 2026-03-22
- [x] SDLC Gate Enforcement + Parallel Agents — /plan, backlog-first,
  pre-flight gates, zie-memory deep integration — 2026-03-22
- [x] Initial plugin scaffolding — hooks, commands, skills, templates —
  2026-03-22
- [x] Project initialized with zie-framework — 2026-03-22

---

## Icebox — Deliberately Deferred

<!-- Good ideas explicitly put on hold. Include reason. -->

<!-- reason: needs more research / out of scope for now / dependency on X -->
