# Changelog

## v1.16.3 — 2026-04-04

### Features

- **proactive-compact-hint** — New Stop hook warns when context usage ≥80% (configurable via `compact_hint_threshold` in .config); prints informational hint to encourage `/compact` before continuing
- **audit-mcp-check** — `/zie-audit` Agent 2 now detects unused MCP servers configured in settings.json but never referenced in commands/skills — reports LOW findings to reduce context overhead
- **roadmap-done-rotation** — `/zie-retro` now auto-archives Done items >90 days old to `archive/ROADMAP-archive-YYYY-MM.md` (append-only); keeps 10 most-recent items inline for history
- **implement-skill-dedup** — `/zie-implement` task loop now uses `Skill(zie-framework:tdd-loop)` pointer instead of inline RED/GREEN/REFACTOR prose — reduces duplication, improves maintainability

### Changed

- **sprint-agent-audit** — `/zie-sprint` Phase 3 (IMPLEMENT) replaces Agent spawning with direct Skill invocation for sequential execution — improves clarity, reduces token overhead
- **split-utils-py** — Refactored 737-line `hooks/utils.py` into 5 focused sub-modules: `utils_config`, `utils_safety`, `utils_event`, `utils_io`, `utils_roadmap` — each hook imports only what it needs, improves discoverability and maintainability
- **merge-safety-hooks** — Consolidated `safety-check.py` and `input-sanitizer.py` into single PreToolUse entry in hooks.json — reduces subprocess spawns from 3→2 per Bash call
- **zie-init delegation** — Step 2 (scan + knowledge drift) delegated to Agent(Explore) with JSON output → reduces command size by ~100 lines
- **retro inlining** — `/zie-retro` now does format + docs-sync checks inline (Bash) instead of spawning agents — keeps ADR + ROADMAP agents for file writes only
- **release gate inlining** — `/zie-release` replaces 4 Agent spawns (test-int, test-e2e, lint, visual) with inline parallel Bash execution — saves ~40k tokens per release
- **intent-sdlc early-exit** — `intent-sdlc.py` now exits early when message is clearly non-SDLC (length <5, no SDLC keywords) — reduces processing overhead on casual messages

### Fixed

- **auto-test output truncation** — `auto-test.py` now truncates test output injection to pass/fail summary + first failure block; skips truncation for .md and config files — improves context efficiency
- **rm -rf pattern false positive** — BLOCKS pattern now uses negative lookahead to distinguish `rm -rf ./` (bare dot, blocked) from `rm -rf ./subdir/` (confirm-wrapped) — fixes over-aggressive blocking

## v1.16.2 — 2026-04-03

### Changed

- **ROADMAP backlog refresh** — Added 12 next-priority items (6 HIGH, 4 MEDIUM,
  2 LOW) for optimization: auto-test output truncation, intent-sdlc early exit,
  release gate inlining, retro format inlining, zie-init delegation, hook
  consolidation, utils modularization, sprint audit, skill dedup, MCP audit,
  proactive compaction
- **Pre-commit hook refactor** — Simplified pre-commit from 45 lines to 2-line
  stub; version drift, bandit SAST, markdownlint checks moved to CI pipeline

## v1.16.1 — 2026-04-02

### Fixed
- **Qwen3-coder-next compatibility** — Fixed `async: true` hooks (hooks.json) → `background: true` for session-learn.py, session-cleanup.py, subagent-stop.py
- **safety_check_agent.py CLI fallback** — Moved `claude` CLI check to `evaluate()` entry point for graceful regex fallback when CLI unavailable
- **test_test_ci skipping** — Skip test when sitecustomize.py unavailable (subprocess hook coverage not available)

### Changed
- **hooks.json protocol** — Replaced `async` with `background` for all Stop hooks
- **Test suite** — Updated `test_architecture_cleanup.py` to check `background` instead of `async`

## v1.16.0 — 2026-04-01

### Fixed
- **Hook timing instrumentation** — Added `log_hook_timing()` utility and structured session execution logs (`/tmp/zie-{session_id}/timing.log`) to track hook performance and diagnose slow paths
- **Environment file permissions** — CLAUDE_ENV_FILE written by `session-resume.py` now set to mode 0o600 (restrictive) per security hardening guidelines
- **Input validation hardening** — Extended dangerous compound regex in `input-sanitizer.py` to guard bare braces (`{` / `}`) alongside existing metachar guards
- **Test boundary case coverage** — Added 6 edge case tests for ADR summary extraction (pipe escaping, truncation at max length, multi-sentence truncation)
- **Weak test assertions** — Replaced ~335 weak keyword-presence checks with structural assertions (section ordering, header presence, frontmatter properties)
- **Safety agent command length** — Added MAX_CMD_CHARS (4096) truncation with marker in `safety_check_agent.py` to prevent oversized prompts
- **Coverage measurement fix** — Adjusted coverage gate from 55% to 48% (ADR-037 updated); documents environmental constraint (sitecustomize.py unavailability in venv)

### Changed
- **Pytest marker consolidation** — Moved `error_path` marker definition from `conftest.py` to `pytest.ini` per pytest best practices
- **Dead code removal** — Removed artifact `if __name__ == "__main__": pass` block from `intent-sdlc.py`
- **Documentation fix** — Corrected doubled "project/project/" path component in README.md directory structure display

## v1.15.0 — 2026-04-01

### Features
- **zie-sprint** — Batch backlog processor for phase-parallel execution: all items through spec/plan together (parallel), then implement (sequential WIP=1), batch release (single tag), single retro. Reduces N releases→1, N retros→1, context loads~25N→1
- **sprint intent detection** — Added 8 patterns to `intent-sdlc.py` for detecting sprint intent from natural language ("sprint", "clear backlog", "ship all", etc.)

## v1.14.2 — 2026-03-30

### Changed
- `make test-fast` no longer runs the full suite when no files have changed — uses `--lfnf=none` so it exits in <1s instead of 2+ minutes
- `make test-fast` fallback (unmapped .py files) now runs raw `pytest tests/unit/` without coverage overhead, instead of `make test-unit`

## v1.14.1 — 2026-03-30

### Changed
- Release Gate 1 now uses `make test-fast` — after a clean implement commit, runs ~0 tests instead of the full suite (~90s → ~1s)
- Word count limits standardized to 1000 across zie-implement/release/retro — eliminates per-file threshold management
- `/zie-implement` passes captured test output to `verify` skill — eliminates the third consecutive `make test-unit` run at end of implement
- `zie-retro` skips docs-sync agent when called immediately after `/zie-release` (already ran during release)
- `zie-retro` pre-loads ROADMAP Next lane in pre-flight — removes second ROADMAP read in "Suggest next"
- `make test-fast` no longer prints `mapfile: command not found` warnings on macOS (bash 3.2 compatibility)

## v1.14.0 — 2026-03-30

### Features
- **agentic-pipeline-v2** — Removed human confirmation gates from spec/plan/retro/release flows; auto-approve when reviewers pass, with override options
- **context-lean-sprint** — ADR session caching (`write_adr_cache`/`get_cached_adrs`) + shared_context bundle in `zie-audit` eliminates redundant reads across agents
- **parallel-release-gates** — Gates 2–4 now spawn simultaneously after Gate 1 passes; docs-sync runs before Gate 1; all failures collected before stopping
- **model-routing-v2** — `zie-release` and `impl-reviewer` use `haiku` with inline `<!-- model: sonnet -->` escalation annotations for judgment-heavy steps
- **workflow-lean** — `--focus` flag for `zie-audit`, `--draft-plan` for `zie-spec`, section-targeted revision loop in `zie-init`
- **dx-polish** — Pipeline stage indicator in `zie-status`, max-iterations next-steps blocks in reviewers, task sizing guidance (S/M/L) in `write-plan`

### Changed
- `zie-retro` and `zie-release` use `general-purpose` agent instead of plugin-specific agents (no plugin reload required)
- `zie-implement` shows agent mode warning when run outside `--agent zie-framework:zie-implement-mode`

## v1.13.0 — 2026-03-30

### Features
- **zie-audit v2** — upgraded from 3 to 7 audit dimensions: Security, Code Health,
  Performance, Structural, Dependency Health, Observability, and a new dedicated
  External Research agent that searches for stack/domain-specific improvements
  (not just bugs). Phase 3 synthesis is now inline (saves 1 agent call). Phase 4
  uses batch backlog prompts (all/select/skip) instead of one-by-one. Scoring
  now categorizes findings as Quick Win, Strategic, or Defer.

### Fixed / Changed
- **5 portability fixes** for using zie-framework in other repos: missing
  `retro-format` and `docs-sync-check` agents now registered; `zie-init` creates
  `dev` branch automatically (required by `make release`); `zie-init` creates
  `.markdownlintignore` so generated SDLC files don't fail pre-commit lint;
  safety hook now allows `git push origin main --tags` (used by `make release`);
  Makefile.local template uses `PYTHON ?= .venv/bin/python3` to avoid
  system/Homebrew version mismatches
- **Plugin marketplace decoupled** — zie-framework and zie-memory no longer
  cross-update each other on release. Each plugin self-contained via
  `github:zierocode/zie-framework` in settings.json. `make release` creates a
  GitHub release directly without touching other repos.

## v1.12.0 — 2026-03-30

### Features

- **Pipeline gate enforcement** — hooks now enforce spec-first ordering:
  PreToolUse blocks `/zie-plan` without an approved spec, and `/zie-implement`
  without an approved plan. Prevents workflow shortcuts.
- **ADR session cache** — mtime-keyed cache in `utils.py` eliminates redundant
  ADR file loads across reviewer calls in the same session.
- **ADR auto-summarization** — `/zie-retro` now generates `ADR-000-summary.md`
  when ADR count exceeds 30, keeping context windows manageable.
- **User onboarding orientation** — `SessionStart` hook warns on knowledge drift;
  `/zie-init` prints SDLC pipeline summary on first run.
- **make test-fast / make test-ci** — two-tier test suite: fast dev loop
  (changed files + last-failed) vs full suite with coverage gate.
- **Hook resilience tests** — error-path coverage for all 10 production hooks;
  new `check_error_path_coverage.py` enforces ≥1 error-path test per hook.
- **ROADMAP Done compaction** — `compact_roadmap_done()` in utils auto-archives
  Done entries older than 6 months when count exceeds 20 (runs in `/zie-retro`).
- **Hook config hardening** — `validate_config()` + `CONFIG_SCHEMA` give typed
  defaults for all 4 timeout keys; auto-test gains wall-clock kill guard.
- **CONFIG_DEFAULTS centralization** — single source of truth for all 7 config
  keys; no more inline `config.get("key", default)` scattered across hooks.
- **zie-init single-pass scan** — Explore agent now returns `migratable_docs`
  as part of its report; step 2h reads from agent output instead of rescanning.
- **make archive-prune** — 90-day TTL rotation for `zie-framework/archive/`;
  guard skips pruning on projects with fewer than 20 archived files; integrated
  into `/zie-retro` post-release cleanup.
- **make clean coverage artifacts** — `.coverage`, `coverage.xml`, `htmlcov/`
  now removed by `make clean`.

### Fixed / Changed

- Retro no longer double-reads ROADMAP; release docs-sync fallback is now
  non-blocking (graceful degradation instead of hard stop).
- Coverage gate lowered from 50% to 43% to reflect actual measurable coverage
  without subprocess hook instrumentation (`coverage sitecustomize` removed in
  coverage 7.x).

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
