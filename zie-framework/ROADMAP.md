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
<!-- Order: Critical → High → Medium (Security/Arch/Quality/Docs/Standards) → Low -->
<!-- Dependency order: toctou before symlink; redos before recompile; -->
<!--   session-learn-concurrent before urllib-dedup; dependabot before signed-releases -->

<!-- CRITICAL — moved to Now -->

<!-- HIGH — moved to Now -->

<!-- MEDIUM — Security/Arch -->

<!-- MEDIUM — Quality -->
<!-- moved to Now: Strengthen no-crash assertions -->
<!-- moved to Now: parse_roadmap_now edge cases -->
<!-- moved to Now: project_tmp_path edge cases -->

<!-- MEDIUM — Docs — moved to Now -->

<!-- MEDIUM — Standards -->
<!-- moved to Now: Dependabot setup -->

<!-- LOW — Lean -->

<!-- LOW — Quality -->

<!-- LOW — Docs/Standards -->

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->
<!-- Source: Deep Claude Code integration research — 2026-03-24 -->

<!-- CRITICAL — Core UX breakage -->
- [ ] PreCompact/PostCompact WIP preservation — [backlog](backlog/prepostcompact-wip-preservation.md) | [spec](specs/2026-03-24-prepostcompact-wip-preservation-design.md)
- [ ] UserPromptSubmit SDLC context injection — [backlog](backlog/userpromptsubmit-sdlc-context.md) | [spec](specs/2026-03-24-userpromptsubmit-sdlc-context-design.md)

<!-- HIGH — Significant quality/UX improvement -->
- [ ] Reviewer skills → custom agents with persistent memory — [backlog](backlog/reviewer-agents-memory.md) | [spec](specs/2026-03-24-reviewer-agents-memory-design.md)
- [ ] Skills frontmatter hardening (disable-model-invocation, user-invocable,
  effort) — [backlog](backlog/skills-frontmatter-hardening.md) | [spec](specs/2026-03-24-skills-frontmatter-hardening-design.md)
- [ ] SessionStart CLAUDE_ENV_FILE config injection — [backlog](backlog/sessionstart-env-file.md) | [spec](specs/2026-03-24-sessionstart-env-file-design.md)
- [ ] SubagentStart SDLC context injection — [backlog](backlog/subagentstart-sdlc-context.md) | [spec](specs/2026-03-24-subagentstart-sdlc-context-design.md)
- [ ] PermissionRequest auto-approve safe SDLC operations — [backlog](backlog/permission-request-auto-approve.md) | [spec](specs/2026-03-24-permission-request-auto-approve-design.md)

<!-- MEDIUM — Meaningful improvements -->
- [ ] PostToolUse additionalContext test file hints — [backlog](backlog/posttooluse-additionalcontext.md) | [spec](specs/2026-03-24-posttooluse-additionalcontext-design.md)
- [ ] Stop hook uncommitted work guard — [backlog](backlog/stop-uncommitted-guard.md) | [spec](specs/2026-03-24-stop-uncommitted-guard-design.md)
- [ ] PreToolUse updatedInput path sanitization + rewriting — [backlog](backlog/pretooluse-input-modification.md) | [spec](specs/2026-03-24-pretooluse-input-modification-design.md)
- [ ] PostToolUseFailure debugging context injection — [backlog](backlog/posttoolusefailure-debug-context.md) | [spec](specs/2026-03-24-posttoolusefailure-debug-context-design.md)
- [ ] Skills context:fork for isolated reviewer execution — [backlog](backlog/skills-fork-context.md) | [spec](specs/2026-03-24-skills-fork-context-design.md)
- [ ] Skills !`cmd` bash injection for live context — [backlog](backlog/skills-bash-injection.md) | [spec](specs/2026-03-24-skills-bash-injection-design.md)
- [ ] SubagentStop capture + resume subagent pattern — [backlog](backlog/subagent-lifecycle-hooks.md) | [spec](specs/2026-03-24-subagent-lifecycle-hooks-design.md)
- [ ] Plugin settings.json defaults + CLAUDE_PLUGIN_DATA storage — [backlog](backlog/plugin-settings-defaults.md) | [spec](specs/2026-03-24-plugin-settings-defaults-design.md)
- [ ] TaskCompleted quality gate hook — [backlog](backlog/taskcompleted-validation.md) | [spec](specs/2026-03-24-taskcompleted-validation-design.md)
- [ ] type:"agent" hooks for smart safety validation — [backlog](backlog/agent-type-hooks.md) | [spec](specs/2026-03-24-agent-type-hooks-design.md)

<!-- LOW — Polish -->
- [ ] Velocity tracking — `/zie-status` shows throughput from git tags — [backlog](backlog/velocity-tracking.md)
- [ ] Retro → Next active loop — surface top backlog candidate after retro — [backlog](backlog/retro-next-active-loop.md)
- [ ] impl-reviewer risk-based invocation — skip reviewer on low-risk tasks — [backlog](backlog/impl-reviewer-risk-based.md)
- [ ] Implement loop inline guidance + parallel tasks — remove per-task skill calls, parallelize by default — [backlog](backlog/implement-guidance-inline.md)
- [ ] Reviewer fail-fast — all issues in one pass, 2 total iterations — [backlog](backlog/reviewer-fail-fast.md)
- [ ] Retro living docs sync — retro systematically updates CLAUDE.md + README.md — [backlog](backlog/retro-living-docs-sync.md)
- [ ] /zie-audit enhancements — hard data (coverage/CVE/complexity) + historical diff + auto-fix — [backlog](backlog/zie-audit-enhancements.md)
- [ ] Skills advanced features ($ARGUMENTS[N], session vars, supporting files)
  — [backlog](backlog/skills-advanced-features.md) | [spec](specs/2026-03-24-skills-advanced-features-design.md)
- [ ] StopFailure API error logging — [backlog](backlog/stopfailure-logging.md) | [spec](specs/2026-03-24-stopfailure-logging-design.md)
- [ ] ConfigChange CLAUDE.md drift detection — [backlog](backlog/configchange-drift-detection.md) | [spec](specs/2026-03-24-configchange-drift-detection-design.md)
- [ ] Agent isolation:worktree + background:true parallel review — [backlog](backlog/agent-worktree-isolation.md) | [spec](specs/2026-03-24-agent-worktree-isolation-design.md)
- [ ] Plugin .mcp.json bundle zie-memory server — [backlog](backlog/plugin-mcp-bundle.md) | [spec](specs/2026-03-24-plugin-mcp-bundle-design.md)
- [ ] Notification hook permission dialog intercept — [backlog](backlog/notification-hook-intercept.md) | [spec](specs/2026-03-24-notification-hook-intercept-design.md)
- [ ] Session-wide agent mode (--agent integration) — [backlog](backlog/session-agent-mode.md) | [spec](specs/2026-03-24-session-agent-mode-design.md)
- [ ] model:haiku + effort:low for fast skills — [backlog](backlog/model-haiku-fast-skills.md) | [spec](specs/2026-03-24-model-haiku-fast-skills-design.md)

---

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
