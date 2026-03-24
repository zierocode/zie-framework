# ROADMAP — zie-framework

> Single source of truth for what's being built and why.
> Updated by /zie-backlog (Next), /zie-plan (Ready), /zie-implement (Now),
> /zie-release (Done), /zie-retro (reprioritization).

---

## Now — Active Sprint

<!-- Current feature in progress. One at a time (WIP=1). -->

---

## Ready — Approved Plans

<!-- Approved implementation plans. Ready to build, waiting for WIP slot. -->
<!-- Order: Critical → High → Medium → Low -->

<!-- CRITICAL -->
- [ ] PreCompact/PostCompact WIP preservation — [plan](plans/2026-03-24-prepostcompact-wip-preservation.md) ✓
- [ ] UserPromptSubmit SDLC context injection — [plan](plans/2026-03-24-userpromptsubmit-sdlc-context.md) ✓

<!-- HIGH -->
- [ ] Reviewer skills → custom agents with persistent memory — [plan](plans/2026-03-24-reviewer-agents-memory.md) ✓
- [ ] Skills frontmatter hardening — [plan](plans/2026-03-24-skills-frontmatter-hardening.md) ✓
- [ ] SessionStart CLAUDE_ENV_FILE config injection — [plan](plans/2026-03-24-sessionstart-env-file.md) ✓
- [ ] SubagentStart SDLC context injection — [plan](plans/2026-03-24-subagentstart-sdlc-context.md) ✓
- [ ] PermissionRequest auto-approve safe SDLC operations — [plan](plans/2026-03-24-permission-request-auto-approve.md) ✓

<!-- MEDIUM -->
- [ ] PostToolUse additionalContext test file hints — [plan](plans/2026-03-24-posttooluse-additionalcontext.md) ✓
- [ ] Stop hook uncommitted work guard — [plan](plans/2026-03-24-stop-uncommitted-guard.md) ✓
- [ ] PreToolUse updatedInput path sanitization + rewriting — [plan](plans/2026-03-24-pretooluse-input-modification.md) ✓
- [ ] PostToolUseFailure debugging context injection — [plan](plans/2026-03-24-posttoolusefailure-debug-context.md) ✓
- [ ] Skills context:fork for isolated reviewer execution — [plan](plans/2026-03-24-skills-fork-context.md) ✓
- [ ] Skills !`cmd` bash injection for live context — [plan](plans/2026-03-24-skills-bash-injection.md) ✓
- [ ] SubagentStop capture + resume subagent pattern — [plan](plans/2026-03-24-subagent-lifecycle-hooks.md) ✓
- [ ] Plugin settings.json defaults + CLAUDE_PLUGIN_DATA storage — [plan](plans/2026-03-24-plugin-settings-defaults.md) ✓
- [ ] TaskCompleted quality gate hook — [plan](plans/2026-03-24-taskcompleted-validation.md) ✓
- [ ] type:"agent" hooks for smart safety validation — [plan](plans/2026-03-24-agent-type-hooks.md) ✓

<!-- LOW -->
- [ ] Skills advanced features ($ARGUMENTS[N], session vars, supporting files) — [plan](plans/2026-03-24-skills-advanced-features.md) ✓
- [ ] StopFailure API error logging — [plan](plans/2026-03-24-stopfailure-logging.md) ✓
- [ ] ConfigChange CLAUDE.md drift detection — [plan](plans/2026-03-24-configchange-drift-detection.md) ✓
- [ ] Agent isolation:worktree + background:true parallel review — [plan](plans/2026-03-24-agent-worktree-isolation.md) ✓
- [ ] Plugin .mcp.json bundle zie-memory server — [plan](plans/2026-03-24-plugin-mcp-bundle.md) ✓
- [ ] Notification hook permission dialog intercept — [plan](plans/2026-03-24-notification-hook-intercept.md) ✓
- [ ] Session-wide agent mode (--agent integration) — [plan](plans/2026-03-24-session-agent-mode.md) ✓
- [ ] model:haiku + effort:low for fast skills — [plan](plans/2026-03-24-model-haiku-fast-skills.md) ✓

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

<!-- (All 25 Claude Code deep integration items moved to Ready — 2026-03-24) -->

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
