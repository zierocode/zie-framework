# Components Registry — zie-framework

**Last updated:** 2026-03-30 (v1.13.0)

## Commands

| Command | Input | Output | Dependencies |
| --- | --- | --- | --- |
| /zie-backlog | idea title (optional) | backlog item file | none |
| /zie-spec | backlog slug OR inline idea string | approved spec | spec-design |
| /zie-plan | slug(s) | approved plan in Ready | write-plan skill |
| /zie-implement | (reads ROADMAP Now) | feature tasks | tdd-loop, test-pyr |
| /zie-fix | bug description | regression test + fix | debug, verify |
| /zie-release | (ROADMAP Now) | release tag + ADRs | verify, make release |
| /zie-status | (reads files) | status snapshot | none |
| /zie-resync | (codebase scan) | updated knowledge docs | Agent(Explore) |
| /zie-retro | (reads git log) | ADRs + brain memories | retro-format skill |
| /zie-audit | --focus dim | audit report + backlog | Agent, WebSearch |

## Skills

| Skill | ทำอะไร | Invoked by |
| --- | --- | --- |
| spec-design | Brainstorm → design spec + spec-reviewer loop | /zie-spec |
| spec-reviewer | Phase 1-3 review with context bundle | spec-design |
| write-plan | Spec → task plan + plan-reviewer loop | /zie-plan, spec-design |
| plan-reviewer | Phase 1-3 review with context bundle | write-plan |
| tdd-loop | RED/GREEN/REFACTOR guide | /zie-implement |
| impl-reviewer | Phase 1-3 review with context bundle; `model: sonnet, effort: medium, context: fork` | /zie-implement |
| test-pyramid | Choose test level (unit/int/e2e) | /zie-implement (RED phase) |
| debug | Reproduce → isolate → fix | /zie-implement, /zie-fix |
| verify | Pre-release verification checklist; `context: fork` with optional captured `test_output` | /zie-fix, /zie-release, /zie-implement |
| retro-format | ADR + retro structure; `context: fork` with compact JSON `$ARGUMENTS` | /zie-retro |
| docs-sync-check | Verify CLAUDE.md/README.md match commands/skills/hooks on disk; `context: fork` | /zie-retro, /zie-release |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced, `debounce_ms=0` = disabled); OSError-guarded rglob + c.exists() |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous cmds (exit 2 = block); MAX_MESSAGE_LEN=500 ReDoS guard; whitespace normalised before match |
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
| input-sanitizer.py | PreToolUse:Bash | resolve relative paths → absolute; rewrite dangerous Bash patterns to require confirmation |
| notification-log.py | Notification:permission_prompt\|idle_prompt | log permission + idle events; inject additionalContext on 3+ repeated permission requests |
| safety_check_agent.py | PreToolUse:Bash | agent-based safety check (active when safety_check_mode=agent\|both in .config) |
| sdlc-permissions.py | PermissionRequest | auto-approve safe SDLC Bash operations (make test-unit, git status, etc.) without interrupting Claude |
| stopfailure-log.py | StopFailure | capture API errors and rate-limit notifications to per-project tmp log |
| subagent-stop.py | SubagentStop | capture subagent completion with ID; enables resume-by-ID pattern in same session |
| task-completed-gate.py | TaskCompleted | block on failing tests; warn on uncommitted files at task completion |
| utils.py | (shared library) | read_event(), get_cwd(), load_config() (JSON + validate_config, CONFIG_DEFAULTS, CONFIG_SCHEMA), parse_roadmap_now(), parse_roadmap_section(), parse_roadmap_ready(), compact_roadmap_done(), project_tmp_path(), call_zie_memory_api(), safe_write_tmp() (symlink-safe, atomic write), normalize_command(), safe_project_name(), get_cached_git_status(session_id, key, ttl=5), write_git_status_cache(session_id, key, content), get_cached_adrs(adr_dir, session_id) (mtime-keyed ADR cache), BLOCKS, WARNS, SDLC_STAGES |

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
