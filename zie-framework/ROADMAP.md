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

---

## Next — Prioritized Backlog

<!-- Ready to start. Ordered by priority. -->

<!-- CRITICAL -->
- [ ] safety-check regex bypass via whitespace variations — [audit finding](backlog/audit-safety-check-regex-bypass.md)

<!-- HIGH -->
- [ ] TOCTOU race condition on /tmp debounce file — [audit finding](backlog/audit-toctou-tmp-race.md)
- [ ] Symlink attack on /tmp state files — [audit finding](backlog/audit-symlink-tmp-attack.md)
- [ ] Add Bandit/Semgrep SAST to CI pipeline — [audit finding](backlog/audit-bandit-sast-ci.md)
- [ ] file_path from hook event not validated within cwd — [audit finding](backlog/audit-filepath-cwd-validation.md)

<!-- MEDIUM — Security -->
- [ ] session-cleanup reimplements safe_project sanitization
  outside utils — [audit finding](backlog/audit-safe-project-dedup.md)
- [ ] intent-detect recompiles 96 regex patterns per event
  (ReDoS surface) — [audit finding](backlog/audit-intent-detect-redos.md)
- [ ] session-learn concurrent file write without lock — [audit finding](backlog/audit-session-learn-concurrent-write.md)

<!-- MEDIUM — Lean -->
- [ ] Duplicated urllib POST pattern across session-learn
  and wip-checkpoint — [audit finding](backlog/audit-urllib-post-dedup.md)

<!-- MEDIUM — Quality -->
- [ ] Tests write real /tmp paths instead of pytest tmp_path — [audit finding](backlog/audit-tests-tmp-path.md)
- [ ] Fixture naming collision _cleanup_debounce × 3 in auto_test — [audit finding](backlog/audit-fixture-naming-collision.md)
- [ ] Weak "no-crash" assertions don't verify hook behavior — [audit finding](backlog/audit-weak-nocrash-assertions.md)
- [ ] parse_roadmap_now() untested for nested markdown and
  malformed links — [audit finding](backlog/audit-parse-roadmap-edge-cases.md)
- [ ] project_tmp_path() untested for pathological inputs — [audit finding](backlog/audit-project-tmp-path-edge-cases.md)

<!-- MEDIUM — Docs -->
- [ ] PROJECT.md version stale: 1.4.0 vs 1.4.1 — [audit finding](backlog/audit-project-md-version-stale.md)
- [ ] README missing troubleshooting and SECURITY/CHANGELOG
  links — [audit finding](backlog/audit-readme-troubleshooting.md)
- [ ] 10 skills not listed in PROJECT.md components section — [audit finding](backlog/audit-skills-registry-gaps.md)
- [ ] zie-init.md shows deprecated project/decisions.md filename — [audit finding](backlog/audit-zieinit-deprecated-filename.md)

<!-- MEDIUM — Architecture -->
- [ ] Silent JSON config parse failures with no stderr logging — [audit finding](backlog/audit-silent-config-parse-failures.md)
- [ ] Inconsistent exception handling strategy across hooks — [audit finding](backlog/audit-exception-handling-inconsistency.md)
- [ ] intent-detect.py recompiles regex on every invocation — [audit finding](backlog/audit-intent-detect-regex-recompile.md)

<!-- MEDIUM — Standards -->
- [ ] Set up Dependabot for dev dependencies — [audit finding](backlog/audit-dependabot-setup.md)

<!-- LOW — Lean -->
- [ ] Event parsing boilerplate repeated in 7 hooks — [audit finding](backlog/audit-event-parsing-boilerplate.md)
- [ ] CLAUDE_CWD initialization repeated in 6 hooks — [audit finding](backlog/audit-cwd-init-boilerplate.md)
- [ ] parse_section() duplicates parse_roadmap_now logic — [audit finding](backlog/audit-parse-section-dedup.md)
- [ ] Knowledge hash algorithm duplicated in 3 command files — [audit finding](backlog/audit-knowledge-hash-dedup.md)

<!-- LOW — Quality -->
- [ ] wip-checkpoint counter file not guarded against ValueError — [audit finding](backlog/audit-counter-valueerror.md)
- [ ] No test for very long commands in safety-check (ReDoS) — [audit finding](backlog/audit-safety-check-redos-test.md)
- [ ] find_matching_test() edge cases not covered — [audit finding](backlog/audit-find-matching-test-edge-cases.md)

<!-- LOW — Docs -->
- [ ] CHANGELOG references removed commands /zie-ship and /zie-build — [audit finding](backlog/audit-changelog-stale-commands.md)
- [ ] SECURITY.md hardcodes 'zierocode' GitHub username — [audit finding](backlog/audit-security-md-username.md)

<!-- LOW — Architecture -->
- [ ] .gitignore missing evidence/ and .pytest_cache entries — [audit finding](backlog/audit-gitignore-gaps.md)
- [ ] Makefile release target doesn't verify main branch is clean — [audit finding](backlog/audit-makefile-release-branch.md)
- [ ] No signed releases or SLSA provenance — [audit finding](backlog/audit-signed-releases.md)

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
