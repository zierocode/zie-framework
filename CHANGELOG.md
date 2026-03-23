# Changelog

## v1.4.1 — 2026-03-23

### Fixed

- **Safety hooks** — PreToolUse `exit(2)` was silently ineffective (was
  `exit(1)`). All 9 block patterns now correctly trigger Claude Code's block
  signal. `rm -rf ./`, force-push to main, `--no-verify`, DROP DATABASE etc.
  are now actually blocked, not just logged.
- **Hook URL validation** — `session-learn.py` and `wip-checkpoint.py` had
  a hardcoded `https://memory.zie-agent.cloud` fallback. Replaced with an
  empty default + `if not api_url.startswith("https://")` guard so hooks
  never silently call an unexpected endpoint.
- **intent-detect** — Prompt that starts with `/zie-*` command text was not
  being skipped; also now skips YAML frontmatter (starts with `---`) and
  messages longer than 500 chars to avoid false-positive intent suggestions.

### Changed

- **`hooks/utils.py`** — New shared library with `parse_roadmap_now()` and
  `project_tmp_path()`. All hooks that read ROADMAP or write to `/tmp` now
  use these helpers — eliminates 40+ lines of duplicated inline logic and
  prevents cross-project `/tmp` file collisions when multiple projects use
  the framework simultaneously.
- **`hooks/session-cleanup.py`** — New Stop hook that deletes project-scoped
  `/tmp` files at session end, so stale debounce/counter state from one
  session never bleeds into the next.
- **Pattern pre-compilation** — `intent-detect.py` now compiles all regex
  patterns once at module load (`COMPILED_PATTERNS`) instead of recompiling
  on every keystroke, improving runtime safety and performance.
- **Silent exception logging** — All `except Exception: pass` swallowed
  errors in hooks now log to stderr for visibility without breaking hook
  safety contract.
- **Hook output protocol** — `hooks/hooks.json` now documents the expected
  stdout format for each event type via `_hook_output_protocol` key.

### Tests

- **290 unit tests** (was 258 pre-sprint). New coverage:
  - `test_utils.py` — `parse_roadmap_now` + `project_tmp_path` (11 tests)
  - `test_session_cleanup.py` — Stop hook file cleanup (5 tests)
  - `test_docs_standards.py` — plugin.json sync, ADR numbering, SECURITY.md,
    .cz.toml, README references, CHANGELOG translation (21 tests)
  - Autouse `/tmp` teardown fixtures across all hook test classes
  - `TestIntentDetectHappyPath` assertions upgraded to JSON parse
  - `TestFindMatchingTest` — `find_matching_test()` importable + direct tests
  - `TestAutoTestDebounceBoundary` + `TestWipCheckpointRoadmapEdgeCases`

### Docs

- `SECURITY.md` — added vulnerability reporting and responsible disclosure
  policy (90-day embargo).
- `.cz.toml` — commitizen config for conventional commits with 9 commit types.
- `project/context.md` — ADR headers canonicalized from `D-NNN` to `ADR-NNN`.
- `project/architecture.md` — updated timestamp and added Version History
  Summary section.
- `CHANGELOG.md v1.1.0` — translated from Thai to English.
- `Makefile` — added `sync-version` target; `.githooks/pre-commit` now checks
  version drift before markdownlint.

## v1.4.0 — 2026-03-23

### Features

- **/zie-audit** — New 5-phase project health command. Builds a
  `research_profile` from your codebase, runs 5 parallel agents across
  9 dimensions (Security, Lean, Quality, Docs, Architecture + Performance,
  Dependency Health, Developer Experience, Standards), fetches external
  benchmarks via WebSearch/WebFetch, scores each dimension /100, and
  presents a ranked findings report. You select which findings to push
  into backlog + ROADMAP. Supports `--focus <dim>` for scoped audits.

### Fixed

- **/zie-implement** — Removed stale `/zie-plan "idea"` reference (now
  correctly points to `/zie-spec`). Added explicit commit step after all
  tasks complete so feature code lands on `dev` before release.
- **/zie-release** — Replaced double-verify pattern with inline TODO +
  secrets scan to eliminate redundant verify call at release time.
- **Makefile** — `make release` now folds plugin.json version bump into
  the release commit via `--amend` instead of creating a separate commit.

## v1.3.0 — 2026-03-23

### Features

- **Quick spec mode** — `/zie-spec "idea"` accepts inline ideas directly,
  no backlog file needed. Detects spaces in argument, derives slug, jumps
  straight to spec-design.
- **Hybrid release** — `/zie-release` delegates publish to `make release
  NEW=<v>`. Makefile templates ship a `ZIE-NOT-READY` skeleton; `/zie-init`
  negotiates a project-appropriate skeleton on first run. Readiness gate
  prevents accidental skeleton execution.
- **Reviewer context bundles** — All three reviewers gain a Phase 1
  context load (named files, ADRs, project/context.md, ROADMAP) and Phase 3
  checks: file existence, ADR conflict, ROADMAP conflict, pattern match.

### Fixed

- `project/decisions.md` renamed to `project/context.md` — avoids naming
  collision with `decisions/` ADR directory. All templates + tests updated.
- `/zie-init` deep scan `knowledge_hash` now stable (dir tree + file counts
  + config files SHA-256). Used by `/zie-resync` for drift detection.
- Post-release pipeline audit: 33 issues (6 critical, 16 important, 11 minor)
  fixed across all 10 commands, 10 skills, and hooks. ADR-003 + ADR-004
  written.

### Changed

- SDLC pipeline redesigned to 6 stages with reviewer quality gates at every
  handoff. `superpowers_enabled` removed — framework is fully self-contained.
- Markdownlint: default config (MD013 line-length no longer overridden).

## v1.2.0 — 2026-03-23

### Features

- **6-stage SDLC pipeline** — replaced 3-stage (idea/build/ship) with
  backlog→spec→plan→implement→release→retro; single-responsibility commands
- **Reviewer quality gates** — `spec-reviewer`, `plan-reviewer`, `impl-reviewer`
  skills dispatch as subagents at each handoff (max 3 iterations → surface to human)
- **zie-init deep scan** — Agent(Explore) scan on existing projects populates
  PROJECT.md and project/* with real data instead of placeholder templates
- **Knowledge drift detection** — `knowledge_hash` stored at init/resync time;
  `/zie-status` warns when project files changed outside SDLC process
- **/zie-resync command** — manual trigger for full codebase rescan + doc update

### Fixes

- Remove all `superpowers_enabled` references — framework fully self-contained
- Fix markdownlint errors across all .md files; add pre-commit lint gate
- Update intent-detect hook for new pipeline command names

### Docs

- ADR D-006: Remove superpowers dependency
- ADR D-007: 6-stage SDLC pipeline with reviewer quality gates
- ADR-001: Reviewer skills as dispatched subagents
- ADR-002: markdownlint pre-commit gate

---

## v1.1.0 — 2026-03-22

### Features

- **Knowledge Architecture** — Every project using zie-framework gets
  `PROJECT.md` (hub) and `project/architecture.md`, `project/components.md`,
  `project/decisions.md` (spokes), auto-generated by `/zie-init` from
  templates — no manual setup required.
- **Project Decisions log** — Records architectural decisions as an
  append-only log with status (Accepted / Superseded). `/zie-retro` syncs
  entries to brain automatically.

### Changed

- **Commands redesigned** — All `/zie-*` commands and skills use
  intent-driven language; phases renamed (e.g., "Write the failing test first
  (RED)").
- **Batch release support** — `[x]` items in the Now lane accumulate pending
  release. `/zie-ship` moves them to Done with a version tag — no need to
  ship features individually. *(command removed in v1.2.0 — use `/zie-release`)*
- **Intent-driven steps** — RED/GREEN/REFACTOR in `/zie-build` are short
  paragraphs instead of bullet micro-steps; config reads collapsed to one
  line. *(command removed in v1.2.0 — use `/zie-implement`)*
- **Version bump suggestion** — `/zie-ship` analyzes the Now lane and git log
  then suggests major/minor/patch with reasoning before confirmation.
- **Human-readable CHANGELOG** — `/zie-ship` drafts the CHANGELOG entry for
  approval before committing.

### Tests

- 165 unit tests covering commands, skills, hooks, and templates (pytest).
