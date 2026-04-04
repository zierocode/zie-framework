# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /zie-backlog (Next), /zie-plan (Ready), /zie-implement (Now),
> /zie-release (Done), /zie-retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->

- [x] truncate-auto-test-output
- [x] intent-sdlc-early-exit
- [x] release-inline-gates
- [x] retro-inline-format
- [x] zie-init-delegate-scan
- [x] merge-safety-hooks
- [x] split-utils-py
- [x] sprint-agent-audit
- [x] implement-skill-dedup

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->

<!-- HIGH -->

<!-- MEDIUM -->

<!-- LOW -->

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->
<!-- Audit 2026-03-26: 53 findings, score 73/100 -->
<!-- Audit 2026-04-01: 9 findings added (4 HIGH, 5 MEDIUM) -->
<!-- Audit 2026-04-02: Qwen3-coder-next deep review — 10 issues -->

<!-- CRITICAL -->

<!-- HIGH -->

- [ ] truncate-auto-test-output — auto-test.py (PostToolUse) injects test output
  into context every Edit/Write; truncate to pass/fail + first failure only,
  skip for *.md/config files
- [ ] intent-sdlc-early-exit — intent-sdlc.py (332 lines) fires every
  UserPromptSubmit; add early-exit when message is clearly non-SDLC
- [ ] release-inline-gates — /zie-release spawns 4 agents to run Bash
  one-liners (make test-int, test-e2e, lint, visual); replace with
  inline Bash parallel execution — saves ~40k+ tokens per release
- [ ] retro-inline-format — /zie-retro spawns 2 agents for text
  processing (retro-format + docs-sync-check); do inline instead,
  keep ADR + ROADMAP agents that write to separate files
- [ ] zie-init-delegate-scan — zie-init.md Step 2 is 143 lines of
  pseudocode for scan+migration; delegate to Agent(Explore) and
  reduce command to a pointer — saves ~100 lines from command file

<!-- MEDIUM -->

- [ ] merge-safety-hooks — consolidate safety-check.py +
  input-sanitizer.py into single hook; reduces subprocess spawn
  from 3→2 on every Bash call
- [ ] split-utils-py — utils.py (737 lines) imported by all 22 hooks;
  split into focused modules so each hook imports only what it needs
- [ ] sprint-agent-audit — review /zie-sprint's 2 background agents;
  if they just orchestrate sequential commands, replace with inline
- [ ] implement-skill-dedup — zie-implement.md lines 51–74 duplicate
  tdd-loop skill (RED-GREEN-REFACTOR); trim to 3-line pointer to skill
- [x] roadmap-done-rotation — /zie-retro should auto-archive Done items
  older than 90 days to archive/ROADMAP-archive-YYYY-MM.md;
  keep 10 most recent inline

<!-- LOW -->

- [ ] audit-mcp-check — add MCP server audit to /zie-audit; warn about
  unused MCP servers that bloat context with tool definitions
- [ ] proactive-compact-hint — in Stop/TaskCompleted hooks, check
  context usage and suggest /compact if above threshold

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->

<!-- HIGH -->

- [x] qwen3-coder-next-deep-review — 10 issues (3 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW):
  - hooks.json async key, claude CLI dependency, symlink handling (CRITICAL)
  - knowledge-hash EXCLUDE_PATHS, intent-sdlc case-insensitive, metachar guard (HIGH)
  - command length, glob filtering, decision fallback (MEDIUM)
  — [plan](plans/2026-04-02-qwen3-coder-next-deep-review.md) [✅ implemented] v1.16.1 2026-04-02

<!-- MEDIUM -->

<!-- LOW -->

---

## Done

<!-- Completed items. Never delete — this is history. -->

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
