# Components Registry — zie-framework

**Last updated:** 2026-04-04 (v1.16.3)

## Commands

| Command | Input | Output | Dependencies |
| --- | --- | --- | --- |
| /zie-backlog | idea title (optional) | backlog item file | none |
| /zie-spec | backlog slug OR inline idea string; `--draft-plan` flag | approved spec + optional plan | spec-design |
| /zie-plan | slug(s) | approved plan in Ready; auto-approves on reviewer ✅ APPROVED | write-plan skill |
| /zie-implement | (reads ROADMAP Now) | feature tasks | tdd-loop, test-pyr |
| /zie-fix | bug description | regression test + fix | debug, verify |
| /zie-release | (ROADMAP Now) | release tag + ADRs; parallel gates 2-4; haiku model | verify, make release |
| /zie-status | (reads files) | status snapshot | none |
| /zie-resync | (codebase scan) | updated knowledge docs | Agent(Explore) |
| /zie-retro | (reads git log) | ADRs + brain memories | retro-format skill |
| /zie-sprint | (reads ROADMAP Next/Ready) | batch pipeline: spec→plan→implement→release→retro for all items; phase-parallel, dependency-detected | Agent, Skill |
| /zie-audit | `--focus` dim (security,deps,code,perf,structure,obs,external) | audit report + backlog; shared_context bundle | Agent, WebSearch |

## Skills

| Skill | ทำอะไร | Invoked by |
| --- | --- | --- |
| spec-design | Brainstorm → design spec + spec-reviewer loop | /zie-spec |
| spec-reviewer | Phase 1-3 review with context bundle | spec-design |
| write-plan | Spec → task plan + plan-reviewer loop | /zie-plan, spec-design |
| plan-reviewer | Phase 1-3 review with context bundle | write-plan |
| tdd-loop | RED/GREEN/REFACTOR guide | /zie-implement |
| impl-reviewer | Phase 1-3 review with context bundle; `model: haiku` with sonnet escalation for security/arch changes | /zie-implement |
| test-pyramid | Choose test level (unit/int/e2e) | /zie-implement (RED phase) |
| debug | Reproduce → isolate → fix | /zie-implement, /zie-fix |
| verify | Pre-release verification checklist; `context: fork` with optional captured `test_output` | /zie-fix, /zie-release, /zie-implement |
| load-context | Load shared context bundle (ADRs + project/context.md) once per session | /zie-plan, /zie-implement, /zie-sprint |
| reviewer-context | Shared Phase 1 protocol for all reviewer skills (cache-first ADR loading) | spec-reviewer, plan-reviewer, impl-reviewer |
| docs-sync-check | Verify CLAUDE.md/README.md match commands/skills/hooks on disk; `context: fork` | /zie-retro, /zie-release |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced, `debounce_ms=0` = disabled); OSError-guarded rglob + c.exists() |
| safety-check.py | PreToolUse:Write/Edit/Bash | บล็อก dangerous cmds (exit 2 = block); includes metachar injection guard + path traversal checks (input-sanitizer merged in v1.16.3); MAX_MESSAGE_LEN=500 ReDoS guard; whitespace normalised before match |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent → suggest cmd (JSON out) |
| session-resume.py | SessionStart | แสดง project state + active feature |
| failure-context.py | PostToolUseFailure:Bash/Write/Edit | inject SDLC debug context (active task, branch, last commit, quick-fix hint); is_interrupt guard; reads branch/log from session git cache before subprocess |
| stop-guard.py | Stop | บล็อก session หาก uncommitted implementation files ถูกตรวจพบ (hooks, tests, commands, skills, templates); stop_hook_active infinite-loop guard |
| session-learn.py | PostToolUse | สังเกต patterns, บันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain; counter ValueError recovery |
| session-cleanup.py | Stop | ลบ project-scoped /tmp files on exit |
| sdlc-compact.py | PreCompact / PostCompact | snapshot SDLC state before compaction; restore as additionalContext after; reads branch/diff from session git cache before subprocess |
| sdlc-context.py | UserPromptSubmit | inject [sdlc] task/stage/next/tests context into every prompt |
| subagent-context.py | SubagentStart:Explore/Plan | inject active feature slug, first incomplete task, ADR count into research subagents |
| config-drift.py | ConfigChange:project_settings\|user_settings | ตรวจ CLAUDE.md / settings.json / zie-framework/.config drift → inject additionalContext to re-read |
| compact-hint.py | Stop | print /compact hint when context_window usage ≥ compact_hint_threshold (default 0.8); configurable via .config; stop_hook_active infinite-loop guard |
| notification-log.py | Notification:permission_prompt\|idle_prompt | log permission + idle events; inject additionalContext on 3+ repeated permission requests |
| safety_check_agent.py | PreToolUse:Bash | agent-based safety check (active when safety_check_mode=agent\|both in .config) |
| sdlc-permissions.py | PermissionRequest | auto-approve safe SDLC Bash operations (make test-unit, git status, etc.) without interrupting Claude |
| stopfailure-log.py | StopFailure | capture API errors and rate-limit notifications to per-project tmp log |
| subagent-stop.py | SubagentStop | capture subagent completion with ID; enables resume-by-ID pattern in same session |
| task-completed-gate.py | TaskCompleted | block on failing tests; warn on uncommitted files at task completion |
| utils.py | (compatibility shim) | re-exports all symbols from 5 sub-modules for backwards compatibility; split in v1.16.3 |
| utils_config.py | (sub-module) | CONFIG_SCHEMA, CONFIG_DEFAULTS, validate_config(), load_config() |
| utils_safety.py | (sub-module) | BLOCKS (rm -rf bare dot guard, negative lookahead), WARNS, COMPILED_BLOCKS, COMPILED_WARNS, normalize_command() |
| utils_event.py | (sub-module) | read_event(), get_cwd(), sanitize_log_field(), log_hook_timing(), call_zie_memory_api() |
| utils_io.py | (sub-module) | safe_project_name(), project_tmp_path(), get_plugin_data_dir(), persistent_project_path(), is_zie_initialized(), get_project_name(), atomic_write(), safe_write_tmp(), safe_write_persistent() |
| utils_roadmap.py | (sub-module) | SDLC_STAGES, parse_roadmap_now/section/ready/content/done(), compact_roadmap_done(), compute_max_mtime(), is_mtime_fresh(), get/write ADR cache, get/write git status cache |

## Agents

Agent files live in `agents/`. Each is a markdown file with a frontmatter block
that controls Claude Code runtime behavior. The body instructs the agent to
invoke the corresponding skill.

| Agent | Frontmatter | Invoked by | Purpose |
| --- | --- | --- | --- |
| `agents/spec-reviewer.md` | `isolation: worktree` | `spec-design` skill | Review spec from clean committed snapshot |
| `agents/plan-reviewer.md` | `isolation: worktree` | `write-plan` skill | Review plan from clean committed snapshot |
| `agents/impl-reviewer.md` | `background: true` | `/zie-implement` step 6 | Review task impl asynchronously; deferred-check on next iteration |
| `agents/zie-implement-mode.md` | `permissionMode: acceptEdits`, `tools: all` | `--agent zie-framework:zie-implement-mode` | TDD session agent — SDLC context, WIP=1, tdd-loop + test-pyramid preload |
| `agents/zie-audit-mode.md` | `permissionMode: plan`, `tools: [Read, Grep, Glob, WebSearch]` | `--agent zie-framework:zie-audit-mode` | Read-only analysis session; findings surfaced as backlog candidates |

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
| `hooks/knowledge-hash.py` | Compute SHA-256 of project structure for drift detection. Called by `make resync` / `/zie-resync`. Not registered in hooks.json. |
| `scripts/test_fast.sh` | Fast TDD feedback loop — runs pytest on changed files + `--lf`. Invoked by `make test-fast`. |
