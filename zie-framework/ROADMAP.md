# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /zie-backlog (Next), /zie-plan (Ready), /zie-implement (Now),
> /zie-release (Done), /zie-retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->

- [x] type:"agent" hooks for smart safety validation — [plan](plans/2026-03-24-agent-type-hooks.md)
- [x] Skills advanced features ($ARGUMENTS[N], session vars, supporting files) — [plan](plans/2026-03-24-skills-advanced-features.md)
- [x] StopFailure API error logging — [plan](plans/2026-03-24-stopfailure-logging.md)
- [x] ConfigChange CLAUDE.md drift detection — [plan](plans/2026-03-24-configchange-drift-detection.md)
- [x] TaskCompleted quality gate hook — [plan](plans/2026-03-24-taskcompleted-validation.md)
- [x] Plugin settings.json defaults + CLAUDE_PLUGIN_DATA storage — [plan](plans/2026-03-24-plugin-settings-defaults.md)
- [x] PreCompact/PostCompact WIP preservation — [plan](plans/2026-03-24-prepostcompact-wip-preservation.md)
- [x] UserPromptSubmit SDLC context injection — [plan](plans/2026-03-24-userpromptsubmit-sdlc-context.md)
- [x] Reviewer skills → custom agents with persistent memory — [plan](plans/2026-03-24-reviewer-agents-memory.md)
- [x] Skills frontmatter hardening — [plan](plans/2026-03-24-skills-frontmatter-hardening.md)
- [x] SessionStart CLAUDE_ENV_FILE config injection — [plan](plans/2026-03-24-sessionstart-env-file.md)
- [x] SubagentStart SDLC context injection — [plan](plans/2026-03-24-subagentstart-sdlc-context.md)
- [x] PermissionRequest auto-approve safe SDLC operations — [plan](plans/2026-03-24-permission-request-auto-approve.md)
- [x] PostToolUse additionalContext test file hints — [plan](plans/2026-03-24-posttooluse-additionalcontext.md)
- [x] Stop hook uncommitted work guard — [plan](plans/2026-03-24-stop-uncommitted-guard.md)
- [x] PreToolUse updatedInput path sanitization + rewriting — [plan](plans/2026-03-24-pretooluse-input-modification.md)
- [x] PostToolUseFailure debugging context injection — [plan](plans/2026-03-24-posttoolusefailure-debug-context.md)
- [x] Skills context:fork for isolated reviewer execution — [plan](plans/2026-03-24-skills-fork-context.md)
- [x] Skills !`cmd` bash injection for live context — [plan](plans/2026-03-24-skills-bash-injection.md)
- [x] SubagentStop capture + resume subagent pattern — [plan](plans/2026-03-24-subagent-lifecycle-hooks.md)

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->

<!-- HIGH -->

<!-- MEDIUM -->

<!-- LOW -->


- [ ] Agent isolation:worktree + background:true parallel review — [plan](plans/2026-03-24-agent-worktree-isolation.md) ✓
- [ ] Plugin .mcp.json bundle zie-memory server — [plan](plans/2026-03-24-plugin-mcp-bundle.md) ✓
- [ ] Notification hook permission dialog intercept — [plan](plans/2026-03-24-notification-hook-intercept.md) ✓
- [ ] Session-wide agent mode (--agent integration) — [plan](plans/2026-03-24-session-agent-mode.md) ✓
- [ ] model:haiku + effort:low for fast skills — [plan](plans/2026-03-24-model-haiku-fast-skills.md) ✓

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

<!-- (All 25 Claude Code deep integration items moved to Ready — 2026-03-24) -->

<!-- PIPELINE QUALITY -->
- [ ] impl-reviewer risk-based invocation — skip reviewer on low-risk tasks — [backlog](backlog/impl-reviewer-risk-based.md)
- [ ] Reviewer fail-fast — all issues in one pass, 2 total iterations — [backlog](backlog/reviewer-fail-fast.md)
- [ ] Reviewer terse output — approved = 1 line, issues = bullets only — [backlog](backlog/reviewer-terse-output.md)
- [ ] Reviewer shared context bundle — load ADRs + context.md once per session — [backlog](backlog/reviewer-shared-context.md)
- [ ] plan-reviewer dependency hints — suggest depends_on annotations for independent tasks — [backlog](backlog/plan-reviewer-dependency-hints.md)

<!-- IMPLEMENT LOOP -->
- [ ] Implement loop inline guidance + parallel tasks — remove per-task skill calls, parallelize by default — [backlog](backlog/implement-guidance-inline.md)
- [ ] Plan lazy loading — read task detail only when that task starts — [backlog](backlog/plan-lazy-loading.md)
- [ ] Progress visibility — phase/step counters for all long-running commands — [backlog](backlog/progress-visibility.md)

<!-- SPEC / PLAN -->
- [ ] spec-design fast path — skip clarifying questions for complete backlog items — [backlog](backlog/spec-design-fast-path.md)
- [ ] spec-design batch section approval — write all sections once, single review — [backlog](backlog/spec-design-batch-approval.md)
- [ ] verify scoped mode — tests-only scope for bug fix path — [backlog](backlog/verify-scoped-mode.md)

<!-- TOKEN / CONTEXT REDUCTION -->
- [ ] Skill content pruning — remove examples + prose from all 10 skills — [backlog](backlog/skill-content-pruning.md)
- [ ] ROADMAP.md section-aware reads — each command reads only needed sections — [backlog](backlog/roadmap-section-aware-reads.md)
- [ ] Session-resume compression — hook output 20+ lines → 4 lines — [backlog](backlog/session-resume-compression.md)

<!-- AUDIT -->
- [ ] /zie-audit enhancements — hard data (coverage/CVE/complexity) + historical diff + auto-fix — [backlog](backlog/zie-audit-enhancements.md)
- [ ] /zie-audit parallel external research — parallelize 15 WebSearch calls in Phase 3 — [backlog](backlog/audit-parallel-research.md)

<!-- WORKFLOW / SDLC -->
- [ ] Velocity tracking — `/zie-status` shows throughput from git tags — [backlog](backlog/velocity-tracking.md)
- [ ] Retro → Next active loop — surface top backlog candidate after retro — [backlog](backlog/retro-next-active-loop.md)
- [ ] Retro living docs sync — retro systematically updates CLAUDE.md + README.md — [backlog](backlog/retro-living-docs-sync.md)

## Later — Someday / Maybe

<!-- Good ideas, not yet prioritized. -->

- [ ] Fix markdownlint-cli@0.48.0 in pre-commit — currently broken (always
  shows help, exits 0); pin to working version or switch to markdownlint-cli2
- [ ] CI/CD via GitHub Actions (run pytest on push)
- [ ] Plugin versioning strategy (semver auto-bump on ship)
- [ ] Integration test: mock Claude Code hook events end-to-end

---

## Done

<!-- Completed items. Never delete — this is history. -->

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
