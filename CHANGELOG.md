# Changelog

## v1.11.1 — 2026-03-29

### Changed
- Git subprocess calls in `failure-context.py` and `sdlc-compact.py` now read from
  a session-scoped file cache before spawning a process — reduces redundant git calls
  on hot paths during active editing sessions.
- Test assertions across 5 hook test files now verify observable side-effects
  (stdout content, file existence, counter values) rather than just exit code — catches
  regressions that previously would have silently passed.

### Docs
- `safety_check_mode` config key is now documented in `CLAUDE.md` with all three
  valid values (`"regex"`, `"agent"`, `"both"`) and their tradeoffs.

## v1.11.0 — 2026-03-27

### Features

- **Archive strategy** — `make archive` moves shipped SDLC artifacts (backlog/specs/plans)
  to `zie-framework/archive/` after release; `/zie-release` now includes archive step;
  keeps active directories lean; idempotent (ADR-023)
- **`/zie-implement` pre-flight guard** — stops execution when ROADMAP.md is missing,
  WIP task is active in Now lane, or Ready lane has no approved plan; guides user to
  correct next command
- **`parse_roadmap_ready()`** — new utility in `hooks/utils.py` mirroring
  `parse_roadmap_now()` for extracting the Ready lane
- **Parallel ADR + ROADMAP update in `/zie-retro`** — ADR write and ROADMAP update
  now launched as concurrent background Agents; failure mode documented

### Changed

- **Effort routing** — `write-plan` SKILL.md downgraded from `effort: high` to `effort: medium`;
  `effort: high` reserved exclusively for `spec-design` (ADR-022)
- **CI hardening** — `make test` → `make test-unit` in `.github/workflows/ci.yml`;
  integration tests require a live Claude session and are excluded from CI
- **Token trim** — redundant intro paragraphs removed from `/zie-implement`, `/zie-release`,
  `/zie-retro`; verbose ASCII table example in retro replaced with compact inline format
- **Security** — `sdlc-permissions.py` metachar guard blocks `;`, `&&`, `||`, `|`, `` ` ``,
  `$(` before allowlist check; atomic write helpers enforce 0o600 permissions;
  `is_zie_initialized()` uses `.is_dir()` not `.exists()` to reject symlink files
- **Dead code removal** — `idle_prompt` Notification handler + hooks.json matcher removed;
  `exec_module` replaced with `SourceFileLoader` pattern in test fixtures

## v1.10.0 — 2026-03-27

### Features

- **Lean & Efficient Optimization** — reduce session token overhead ~47%:
  merged `intent-detect.py` + `sdlc-context.py` into single `intent-sdlc.py`
  hook; added 30s ROADMAP.md session cache; `wip-checkpoint` now runs async
  (background: true); `safety_check_mode` defaults to `regex` (no subagent
  on every tool call); `zie-audit` migrated from 5 Opus agents to 3 Sonnet
  agents + synthesis pass (effort: high → medium, per ADR-021); `zie-retro`
  effort: high → medium; `zie-implement` slimmed 351 → 109 lines; parallel
  agent caps removed from `zie-implement` and `zie-plan` — `depends_on` and
  file-conflict detection govern serialization instead; `make archive-plans`
  target added for plans/ housekeeping
- **Hybrid Release** — generic base `Makefile` + `Makefile.local` hook
  architecture; project-specific publish steps live in `Makefile.local`,
  keeping the framework Makefile shareable across projects
- **Single Zierocode Marketplace** — `ZIEROCODE_MKT` sync added to release
  pipeline; one command now publishes to the marketplace

## v1.9.0 — 2026-03-25

### Features

- **hook-events JSON schema** (`hooks/hook-events.schema.json`): formal JSON
  Schema for the Claude Code hook event envelope — documents `tool_name`,
  `tool_input`, `tool_response`, `is_interrupt`, `session_id` fields with types
- **SDLC_STAGES canonical list** in `utils.py`: single source of truth for
  stage names used by `intent-detect` and `sdlc-context`
- **`normalize_command()` utility**: deduped whitespace-normalization used by
  `safety-check`, `safety_check_agent`, and `sdlc-permissions` — no more
  inline `re.sub` copies
- **Configurable TEST_INDICATORS** in `task-completed-gate`: project can set
  `test_indicators` in `.config` to override which file patterns are considered
  test files (e.g. `.spec.`, `.test.`, `_test.`)
- **Async Stop hooks**: `session-learn.py` and `session-cleanup.py` now run
  with `"async": true` — session end no longer blocks on slow network calls

### Fixed

- **`load_config()` now parses JSON** (was silently broken — `.config` is
  JSON but old code used a KEY=VALUE parser, so `safety_check_mode` was never
  read from config)
- **Shell injection in `input-sanitizer.py`**: restricted allowed characters
  in path rewrite to prevent injected shell metacharacters
- **`/tmp` hardening**: atomic write-then-rename for all tmp files, O_EXCL
  creation, mode `0o600` — eliminates TOCTOU race and predictable-name attacks
- **Path traversal**: replaced `startswith()` with `is_relative_to()` in
  `input-sanitizer.py` — prevents `../` escape from cwd
- **Subprocess timeouts on git calls** in `sdlc-compact.py`: all `git` calls
  now have `timeout=5` to prevent hooks hanging indefinitely
- **Coverage measurement**: `.coveragerc` added; `make test-unit` now correctly
  measures subprocess coverage via `COVERAGE_PROCESS_START`
- **`BLOCKS`/`WARNS` moved to `utils.py`**: `safety_check_agent` no longer
  needs an `importlib` workaround — imports directly; 39-line reduction
- **`safe_project_name()` in `notification-log`**: consistent with all other
  hooks that sanitize project name for use in tmp file paths
- **Log prefix audit**: all deprecated `[zie] warning:` prefixes replaced
  with `[zie-framework] <hook-name>:` across all hooks

### Changed

- `make test-unit` comment clarified to explicitly say "excludes integration tests"
- CLAUDE.md Optional Dependencies table added (pytest, coverage, playwright, zie-memory)
- README.md Skills section added (11 skills documented)
- architecture.md version history updated through v1.9.0

## v1.8.0 — 2026-03-24

### Features

- **docs-sync-check skill**: new `haiku + context:fork` skill that verifies
  `CLAUDE.md` and `README.md` match actual commands/skills/hooks on disk;
  returns structured JSON verdict for callers to act on
- **Parallel quality gates in `/zie-release`**: TODOs/secrets scan and
  docs-sync-check fork immediately after Gate 1 passes, running concurrently
  with Gate 2/3 (integration + e2e) — serial gate count drops from 7 to 5
- **Verify overlap in `/zie-implement`**: `verify` is now forked with captured
  test output immediately after the final `make test-unit`, running in parallel
  with ROADMAP update and `git add` prep — eliminates a full test re-run
- **Parallel forks in `/zie-retro`**: `retro-format` and `docs-sync-check` are
  forked simultaneously while the parent writes ADRs, then results are collected

### Changed

- **impl-reviewer upgraded**: `model: haiku, effort: low` → `model: sonnet,
  effort: medium` — code review is reasoning-heavy; fork already bounds context
  to the changed-files bundle so cost increase is well-bounded
- **verify and retro-format get `context: fork`**: both skills now declare
  `context: fork` with documented `$ARGUMENTS` input format; fall back to
  full inline mode when called without arguments (backward compatible)
- **zie-spec and zie-plan effort lowered**: `effort: high` → `effort: medium`
  — heavy reasoning is delegated to spec-design/write-plan skills; these
  commands are orchestration-only
- **Unofficial `type:` fields removed**: `tdd-loop` (`type: process`),
  `test-pyramid` (`type: reference`), and `retro-format` (`type: reference`)
  — these were non-standard fields not in the Claude Code spec; tests now
  enforce their absence

## v1.7.0 — 2026-03-24

### Features

- **Pipeline speed**: implement loop now inlines guidance and parallelizes
  independent tasks by default — no more per-task skill round-trips
- **Lazy plan loading**: task detail is read only when that task starts,
  cutting context overhead for large plans
- **Terse reviewer output**: approved results in 1 line; issue reports use
  bullets only — no narrative prose
- **Reviewer shared context**: ADRs + context.md loaded once per session,
  not re-read per review pass
- **Reviewer fail-fast**: all issues surfaced in a single pass (max 2 iterations)
- **Risk-based impl-reviewer**: low-risk tasks skip the reviewer gate entirely
- **spec-design fast path**: complete backlog items skip clarifying questions
- **spec-design batch approval**: all spec sections written at once, single review
- **verify scoped mode**: `scope=tests-only` for bug-fix path skips full lint
- **Skill content pruning**: tutorial prose and examples removed from all 10 skills
- **Velocity tracking**: `/zie-status` now shows release throughput from git tags
- **Retro → next loop**: retrospective surfaces top backlog candidate to act on next
- **Retro living docs sync**: retro systematically diffs and updates CLAUDE.md + README.md
- **Session-resume compression**: hook output compressed from 20+ lines to 4 lines
- **Audit hard data**: Phase 1 now collects pytest coverage, radon complexity,
  and pip audit CVE counts before research begins
- **Audit historical diff**: each audit diffs scores against the previous run
- **Audit parallel research**: all Phase 3 WebSearch queries dispatched in a
  single parallel batch instead of a sequential loop
- **Audit auto-fix offer**: low/medium findings trigger a scoped `/zie-fix` offer
- **GitHub Actions CI**: pytest runs automatically on push/PR to main and dev
- **pre-commit markdownlint gate**: `markdownlint-cli2` runs on every commit
- **`make bump`**: atomically bumps VERSION + plugin.json with semver validation
- **Version consistency gate**: `/zie-release` blocks if VERSION and plugin.json
  are out of sync before any tests run
- **63 integration tests**: every hook script tested as a subprocess with a
  realistic Claude Code event payload on stdin

### Fixed

- Hook tests were inheriting session-injected env vars (`ZIE_AUTO_TEST_DEBOUNCE_MS`,
  `ZIE_MEMORY_ENABLED`, `ZIE_TEST_RUNNER`) from the outer Claude Code process,
  causing 9 pre-existing test failures — all test `run_hook()` helpers now
  clear these vars so hooks read from config
- `auto-test.py` debounce guard now correctly treats `debounce_ms=0` as
  "no debounce" (was susceptible to filesystem clock rounding on APFS)

## v1.6.0 — 2026-03-24

### Features

- **Session-wide agent modes** — `zie-implement-mode` (permissionMode: acceptEdits,
  all tools) and `zie-audit-mode` (permissionMode: plan, read-only) agents for
  one-command session setup with SDLC context pre-loaded
- **Plugin MCP bundle** — `.claude-plugin/.mcp.json` auto-registers the zie-memory
  MCP server at plugin load time; brain integration now requires zero per-project setup
- **Agent isolation** — reviewer agents gain `isolation: worktree` (clean committed
  snapshot) and `background: true` (async spawn with deferred-check polling pattern)
- **Notification hook** — logs `permission_prompt` and `idle_prompt` events; injects
  `additionalContext` after 3+ repeated permission requests to help Claude self-unblock
- **ConfigChange drift detection** — detects CLAUDE.md, settings.json, and
  zie-framework/.config changes at session start; warns on config drift
- **Safety check agent type** — `type: "agent"` hook mode with A/B testing support
  via `safety_check_mode` config flag (regex / agent / both)
- **TaskCompleted quality gate** — blocks task completion on failing tests; warns on
  uncommitted files when a task is marked done
- **StopFailure hook** — captures API errors and rate-limit notifications to a
  per-project tmp file for post-session review
- **Plugin settings.json + CLAUDE_PLUGIN_DATA** — persistent storage path for
  plugin-level data; plugin ships reference `settings.json` with defaults
- **PreCompact/PostCompact WIP preservation** — saves active WIP context before
  context compaction and restores it immediately after
- **UserPromptSubmit SDLC context** — injects current feature name and active plan
  into every user prompt turn
- **SubagentStart SDLC context** — injects zie-framework pipeline context into every
  Explore and Plan subagent spawn
- **SubagentStop lifecycle hooks** — captures subagent completion with ID; enables
  resume-by-ID pattern for follow-up questions in the same session
- **SessionStart env file** — reads `CLAUDE_ENV_FILE` at session start for config
  injection and env var fast-paths
- **PermissionRequest auto-approve** — automatically approves safe SDLC Bash
  operations (make test-unit, git status, etc.) without interrupting Claude
- **PostToolUse test file hints** — emits `additionalContext` with the matching test
  file path on every source file save
- **PostToolUseFailure debug context** — injects SDLC debug context into the next
  turn when a tool fails, surfacing likely root causes
- **PreToolUse input sanitizer** — resolves relative paths to absolute; rewrites
  dangerous Bash patterns to require confirmation
- **Stop hook uncommitted guard** — warns before session end when uncommitted
  implementation files are detected
- **Skills context:fork** — spec-reviewer, plan-reviewer, and impl-reviewer now run
  in isolated fork context, preventing reviewer contamination of main context
- **Skills bash injection** — `` !`cmd` `` syntax in skill content injects live shell
  output at invocation time (git log, git status, knowledge hash)
- **Skills frontmatter hardening** — all skills gain `user-invocable`, `allowed-tools`,
  and `effort` fields; Claude Code enforces tool restrictions at runtime
- **Reviewer agents with persistent memory** — reviewer skills converted to custom
  agent definitions with `isolation: worktree` / `background: true` frontmatter
- **Skills advanced features** — `$ARGUMENTS[N]` indexed argument access; zie-audit
  promoted to first-class skill with `reference.md` supporting file

### Changed

- **Full model+effort routing** — all 22 commands and skills now have explicit
  `model` and `effort` frontmatter: `opus` for zie-audit (9-dim analysis),
  `sonnet` for design/build/release, `haiku` for mechanical/checklist tasks
- **MCP canonical tool names** — all zie-memory calls in commands and skills updated
  to canonical `mcp__plugin_zie-memory_zie-memory__*` tool names
- **1101 unit tests** — up from 400 in v1.5.0; full coverage across all new hooks,
  skills, agents, and frontmatter contracts

## v1.5.0 — 2026-03-24

### Security

- **Whitespace normalization** — `safety-check.py` now strips and collapses
  whitespace before pattern matching, closing a bypass where `rm  -rf  /`
  (multi-space) was not caught by the block rules.
- **Symlink attack prevention** — `safe_write_tmp()` in `utils.py` now
  detects symlinks on the target path and refuses to write, blocking an
  attack where a symlink to a sensitive file could be overwritten via
  hook state files.
- **TOCTOU race fix** — debounce file writes (auto-test, wip-checkpoint)
  now use atomic write-then-rename instead of direct `write_text()`,
  eliminating a race condition in concurrent hook invocations.
- **CWD boundary enforcement** — `auto-test.py` resolves and validates
  `file_path` against the project CWD before use; paths outside the
  project are silently ignored.
- **intent-detect ReDoS guard** — Added `MAX_MESSAGE_LEN = 500` cap
  before regex matching; long messages exit early before pattern evaluation.

### Features

- **Bandit SAST** — `make lint` now runs `bandit -r hooks/ -ll` and the
  pre-commit hook gates every commit on bandit passing.
- **Dependabot** — `.github/dependabot.yml` added for automated pip and
  GitHub Actions dependency updates.
- **Signed releases** — `make release` now uses `git tag -s` (GPG-signed
  tags) with clean-tree and branch pre-flight guards.
- **SLSA L1 provenance** — `.github/workflows/release-provenance.yml`
  generates attestations on every tagged release via
  `actions/attest-build-provenance@v1`.

### Changed

- **Shared hook utilities** — `hooks/utils.py` gained `read_event()`,
  `get_cwd()`, `parse_roadmap_section()`, and `call_zie_memory_api()`.
  All 7 hooks now use these helpers; 200+ lines of duplicated boilerplate
  removed across the codebase.
- **`hooks/knowledge-hash.py`** — Knowledge hash computation extracted
  from inline `python3 -c "..."` blocks in `zie-init.md`, `zie-status.md`,
  and `zie-resync.md` into a standalone script.
- **SECURITY.md** — Added fork note to advisory URL and new `## Release
  Signing` section documenting GPG tag verification and SLSA provenance.

### Tests

- 400 unit tests (was 361) — added contract tests for counter ValueError
  recovery, safety-check ReDoS performance bounds, `find_matching_test()`
  edge cases (missing dir, symlinks, permission-denied, empty dir), and
  comprehensive coverage for all new hook utilities.

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
