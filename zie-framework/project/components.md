# Components Registry — zie-framework

**Last updated:** 2026-04-06 (v1.21.0)

## Commands

| Command | Input | Output | Dependencies |
| --- | --- | --- | --- |
| /backlog | idea title (optional) | backlog item file | none |
| /spec | backlog slug OR inline idea string; `--draft-plan` flag | approved spec + optional plan | spec-design |
| /plan | slug(s) | approved plan in Ready; auto-approves on reviewer ✅ APPROVED | write-plan skill |
| /implement | (reads ROADMAP Now) | feature tasks | tdd-loop, test-pyr |
| /fix | bug description | regression test + fix | debug, verify |
| /spike | exploration slug | sandbox in `spike-<slug>/`, FINDINGS.md, no ROADMAP write | none |
| /release | (ROADMAP Now) | release tag + ADRs; parallel gates 2-4; haiku model | verify, make release |
| /status | (reads files) | status snapshot | none |
| /resync | (codebase scan) | updated knowledge docs | Agent(Explore) |
| /retro | (reads git log) | ADRs + brain memories | retro-format skill |
| /sprint | (reads ROADMAP Next/Ready) | batch pipeline: spec+plan→implement→release→retro; Phase 1 as Skill() chain (ADR-060); autonomous_mode=true for unattended run; Phase 4 auto-retro (v1.21.0) | Agent, Skill |
| /audit | `--focus` dim (security,deps,code,perf,structure,obs,external) | thin dispatcher → audit skill (canonical); audit report + backlog (v1.19.0) | audit skill |

## Skills

| Skill | ทำอะไร | Invoked by |
| --- | --- | --- |
| spec-design | Brainstorm → design spec + spec-review loop | /spec |
| review | Parametric reviewer: phase=spec|plan|impl; context bundle passthrough (v1.32.2) | spec-design, write-plan, /implement |
| write-plan | Spec → task plan + plan-review loop | /plan, spec-design |
| tdd-loop | RED/GREEN/REFACTOR guide; enforces "run tests once per phase" (never re-run for different grep — capture once, grep the capture) (v1.18.1) | /implement |
| test-pyramid | Choose test level (unit/int/e2e) | /implement (RED phase) |
| debug | Reproduce → isolate → fix | /implement, /fix |
| verify | Pre-release verification checklist; `context: fork` with optional captured `test_output` | /fix, /release, /implement |
| context | Load shared context bundle (ADRs + project/context.md) + framework reference maps; keyword-filtered ADR cache (v1.32.2) | /plan, /implement, /sprint, /spec, /brainstorm |
| docs-sync | Verify CLAUDE.md/README.md match commands/skills/hooks on disk; `context: fork` | /retro, /release |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced, `debounce_ms=0` = disabled); OSError-guarded rglob + c.exists() |
| safety-check.py | PreToolUse:Write/Edit/Bash | บล็อก dangerous cmds (exit 2 = block); includes metachar injection guard + path traversal checks (input-sanitizer merged in v1.16.3); MAX_MESSAGE_LEN=500 ReDoS guard; whitespace normalised before match |
| intent-sdlc.py | PreToolUse:Bash | intent detection → suggest SDLC command (JSON out); pattern dedup cache; session-level intent flags |
| session-resume.py | SessionStart | แสดง project state + active feature |
| failure-context.py | PostToolUseFailure:Bash/Write/Edit | inject SDLC debug context (active task, branch, last commit, quick-fix hint); is_interrupt guard; reads branch/log from session git cache before subprocess |
| stop-handler.py | Stop | merged stop-guard + compact-hint + stop-pipeline-guard; uncommitted file check, sprint intent nudge, context health nudge; stop_hook_active infinite-loop guard |
| session-learn.py | PostToolUse | สังเกต patterns, บันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain; counter ValueError recovery |
| session-cleanup.py | Stop | ลบ project-scoped /tmp files on exit |
| sdlc-compact.py | PreCompact / PostCompact | snapshot SDLC state before compaction; restore as additionalContext after; reads branch/diff from session git cache before subprocess |
| subagent-context.py | SubagentStart:Explore/Plan | inject active feature slug, first incomplete task, ADR count into research subagents |
| config-drift.py | ConfigChange:project_settings\|user_settings | ตรวจ CLAUDE.md / settings.json / zie-framework/.config drift → inject additionalContext to re-read |
| notification-log.py | Notification:permission_prompt\|idle_prompt | log permission + idle events; inject additionalContext on 3+ repeated permission requests |
| safety_check_agent.py | PreToolUse:Bash | agent-based safety check; merged into safety-check.py inline dispatch (v1.19.0) — no separate file read per Bash call |
| sdlc-permissions.py | PermissionRequest | auto-approve safe SDLC Bash operations (make test-unit, git status, etc.) without interrupting Claude |
| stopfailure-log.py | StopFailure | capture API errors and rate-limit notifications to per-project tmp log |
| subagent-stop.py | SubagentStop | capture subagent completion with ID; enables resume-by-ID pattern in same session |
| task-completed-gate.py | TaskCompleted | block on failing tests; warn on uncommitted files at task completion |
| utils.py | (compatibility shim) | re-exports all symbols from 5 sub-modules for backwards compatibility; split in v1.16.3 |
| utils_config.py | (sub-module) | CONFIG_SCHEMA, CONFIG_DEFAULTS, validate_config(), load_config() |
| utils_safety.py | (sub-module) | BLOCKS (rm -rf bare dot guard, negative lookahead), WARNS, COMPILED_BLOCKS, COMPILED_WARNS, normalize_command() |
| utils_event.py | (sub-module) | read_event(), get_cwd(), sanitize_log_field(), log_hook_timing(), call_zie_memory_api() |
| utils_io.py | (sub-module) | safe_project_name(), project_tmp_path(), get_plugin_data_dir(), persistent_project_path(), is_zie_initialized(), get_project_name(), atomic_write(), safe_write_tmp(), safe_write_persistent() |
| utils_roadmap.py | (sub-module) | SDLC_STAGES, parse_roadmap_now/section/ready/content/done(), compact_roadmap_done(), compute_max_mtime(), is_mtime_fresh(), get/write ADR cache, get/write git status cache, is_track_active(), parse_roadmap_items_with_dates() |
| utils_drift.py | (sub-module) | append_drift_event(), read_drift_count(), close_drift_track() — manages zie-framework/.drift-log NDJSON bypass tracking |
| utils_backlog.py | (sub-module) | infer_tag() (keyword map → auto-tag), find_duplicate_slugs() (≥2-token overlap detection) |
| utils_self_tuning.py | (sub-module) | parse_red_cycle_durations_from_log(), build_tuning_proposals() — generates up to 3 retro config proposals from RED duration + BLOCK history |

## Agents

Agent files live in `agents/`. Each is a markdown file with a frontmatter block
that controls Claude Code runtime behavior. The body instructs the agent to
invoke the corresponding skill.

| Agent | Frontmatter | Invoked by | Purpose |
| --- | --- | --- | --- |
| `agents/builder.md` | `permissionMode: acceptEdits`, `tools: all` | `--agent zie-framework:builder` | TDD session agent — SDLC context, WIP=1, tdd-loop + test-pyramid preload |
| `agents/auditor.md` | `permissionMode: plan`, `tools: [Read, Grep, Glob, WebSearch]` | `--agent zie-framework:auditor` | Read-only analysis session; findings surfaced as backlog candidates |

### Field reference

**`isolation: worktree`** — Claude Code spawns the agent in a temporary git
worktree pointing to `HEAD`. The agent sees only the last committed state;
uncommitted working-tree changes are invisible.

**`background: true`** — Claude Code spawns the agent asynchronously and returns
a handle immediately. The caller continues without blocking. The caller is
responsible for polling the handle and handling `approved` / `issues_found`
states.

## Utility Scripts

Scripts in `hooks/` that are not registered as hook event handlers.

| Script | Purpose |
| --- | --- |
| `hooks/knowledge-hash.py` | Compute SHA-256 of project structure for drift detection. Called by `make resync` / `/resync`. Not registered in hooks.json. |
| `scripts/test_fast.sh` | Fast TDD feedback loop — runs pytest on changed files + `--lf`. Invoked by `make test-fast`. |
