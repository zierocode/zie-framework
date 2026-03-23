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
- [x] counter ValueError contract tests — [plan](plans/2026-03-24-audit-counter-valueerror.md) ✓
- [x] safety-check ReDoS perf tests — [plan](plans/2026-03-24-audit-safety-check-redos-test.md) ✓
- [x] find_matching_test edge cases — [plan](plans/2026-03-24-audit-find-matching-test-edge-cases.md) ✓

<!-- LOW — Docs/Standards -->
- [x] CHANGELOG stale commands annotated — [plan](plans/2026-03-24-audit-changelog-stale-commands.md) ✓
- [x] SECURITY.md fork disclaimer — [plan](plans/2026-03-24-audit-security-md-username.md) ✓
- [x] .gitignore gaps fixed — [plan](plans/2026-03-24-audit-gitignore-gaps.md) ✓
- [x] Makefile release branch guard — [plan](plans/2026-03-24-audit-makefile-release-branch.md) ✓
- [x] Signed releases + SLSA L1 — [plan](plans/2026-03-24-audit-signed-releases.md) ✓

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

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
