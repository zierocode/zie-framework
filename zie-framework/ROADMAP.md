# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /zie-backlog (Next), /zie-plan (Ready), /zie-implement (Now),
> /zie-release (Done), /zie-retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->
- [x] [audit-write-adr-cache-contract](backlog/audit-write-adr-cache-contract.md) — fix write_adr_cache return type contract
- [x] [audit-hook-outer-guard](backlog/audit-hook-outer-guard.md) — outer try/except for session-resume/session-learn/wip-checkpoint
- [x] [audit-pytest-cve-requirements](backlog/audit-pytest-cve-requirements.md) — requirements-dev.txt + CVE pytest pin
- [x] [audit-roadmap-cache-sanitize](backlog/audit-roadmap-cache-sanitize.md) — path injection + cleanup fix

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->

<!-- HIGH -->

<!-- MEDIUM -->
- [x] [audit-playwright-version-check](backlog/audit-playwright-version-check.md) — CVE-2025-59288
  Playwright <1.55.1 MitM installer; no startup version check when playwright_enabled
- [x] [audit-safety-check-regex-precompile](backlog/audit-safety-check-regex-precompile.md) —
  BLOCKS/WARNS recompiled on every PreToolUse:Bash hot path; use COMPILED_PATTERNS pattern
- [x] [audit-readme-sprint-command](backlog/audit-readme-sprint-command.md) — /zie-sprint added
  v1.15.0 but absent from README.md commands table (primary public doc)
- [x] [audit-ruff-lint-gate](backlog/audit-ruff-lint-gate.md) — no Python linter in
  pre-commit/Makefile/CI; ruff is community standard; hooks already use type annotations
- [x] [audit-coverage-gate-raise](backlog/audit-coverage-gate-raise.md) — gate at 43% (ADR-027);
  sitecustomize.py stable; incrementally raise toward community standard 70%
- [x] [audit-knowledge-hash-mtime-gate](backlog/audit-knowledge-hash-mtime-gate.md) — rglob twice
  on every SessionStart; gate on mtime delta to skip recompute
- [x] [audit-subagent-stop-atomic](backlog/audit-subagent-stop-atomic.md) — bare open("a") not
  atomic under concurrent sprint mode; use atomic rename pattern
- [x] [audit-project-md-docs-sync](backlog/audit-project-md-docs-sync.md) — docs-sync-check skill
  absent from PROJECT.md skills table

<!-- LOW -->
- [x] [audit-stopfailure-stderr](backlog/audit-stopfailure-stderr.md) — only rate_limit/billing_error
  surfaced to stderr; context_limit + others silent
- [x] [audit-cache-write-silent-failure](backlog/audit-cache-write-silent-failure.md) — bare
  except:pass in write_roadmap_cache/write_git_status_cache; add stderr log per ADR two-tier
- [x] [audit-ci-matrix](backlog/audit-ci-matrix.md) — CI single ubuntu+3.13 only; add macOS +
  Python 3.11 matrix
- [x] [audit-session-resume-chmod](backlog/audit-session-resume-chmod.md) — CLAUDE_ENV_FILE written
  without 0o600 chmod unlike all other write helpers
- [x] [audit-brace-guard](backlog/audit-brace-guard.md) — bare } not blocked by
  _DANGEROUS_COMPOUND_RE in confirmation wrapper
- [x] [audit-intent-sdlc-dead-code](backlog/audit-intent-sdlc-dead-code.md) — dead
  if __name__=="__main__": pass artifact at lines 335-336
- [x] [audit-adr-summary-tests](backlog/audit-adr-summary-tests.md) — pipe-escaping +
  truncation boundary cases untested in adr_summary.py
- [x] [audit-readme-dir-fix](backlog/audit-readme-dir-fix.md) — doubled project/project/ path
  component in README directory structure
- [x] [audit-weak-keyword-assertions](backlog/audit-weak-keyword-assertions.md) — ~335
  assert "keyword" in content checks; replace with structural assertions
- [x] [audit-hook-timing-log](backlog/audit-hook-timing-log.md) — no hook execution timing;
  append structured entry to session log
- [x] [audit-pytest-markers-consolidate](backlog/audit-pytest-markers-consolidate.md) — error_path
  marker in conftest.py not pytest.ini; consolidate
- [x] [audit-safety-agent-length-cap](backlog/audit-safety-agent-length-cap.md) — no command
  length cap before subagent prompt in safety_check_agent
- [x] [audit-nosec-annotation](backlog/audit-nosec-annotation.md) — nosec B310 in
  call_zie_memory_api has no justification comment; add rationale
- [x] [audit-commitizen-pin](backlog/audit-commitizen-pin.md) — commitizen unpinned; add to
  requirements-dev.txt once audit-pytest-cve-requirements is done

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->
<!-- Audit 2026-03-26: 53 findings, score 73/100 -->
<!-- Audit 2026-04-01: 9 findings added (4 HIGH, 5 MEDIUM) -->

<!-- CRITICAL -->

<!-- HIGH -->

<!-- MEDIUM -->

<!-- LOW -->

## Later — Someday / Maybe

<!-- Good ideas, not yet prioritized. -->

---

## Done

<!-- Completed items. Never delete — this is history. -->

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
