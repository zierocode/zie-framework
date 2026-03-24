# Components Registry — zie-framework

**Last updated:** 2026-03-24

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
| impl-reviewer | Phase 1-3 review with context bundle | /zie-implement |
| test-pyramid | Choose test level (unit/int/e2e) | /zie-implement (RED phase) |
| debug | Reproduce → isolate → fix | /zie-implement, /zie-fix |
| verify | Pre-release verification checklist | /zie-fix, /zie-release |
| retro-format | ADR + retro structure | /zie-retro |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced); OSError-guarded rglob + c.exists() |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous cmds (exit 2 = block); MAX_MESSAGE_LEN=500 ReDoS guard; whitespace normalised before match |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent → suggest cmd (JSON out) |
| session-resume.py | SessionStart | แสดง project state + active feature |
| failure-context.py | PostToolUseFailure:Bash/Write/Edit | inject SDLC debug context (active task, branch, last commit, quick-fix hint); is_interrupt guard |
| stop-guard.py | Stop | บล็อก session หาก uncommitted implementation files ถูกตรวจพบ (hooks, tests, commands, skills, templates); stop_hook_active infinite-loop guard |
| session-learn.py | PostToolUse | สังเกต patterns, บันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain; counter ValueError recovery |
| session-cleanup.py | Stop | ลบ project-scoped /tmp files on exit |
| sdlc-compact.py | PreCompact / PostCompact | snapshot SDLC state before compaction; restore as additionalContext after |
| sdlc-context.py | UserPromptSubmit | inject [sdlc] task/stage/next/tests context into every prompt |
| subagent-context.py | SubagentStart:Explore/Plan | inject active feature slug, first incomplete task, ADR count into research subagents |
| config-drift.py | ConfigChange:project_settings\|user_settings | ตรวจ CLAUDE.md / settings.json / zie-framework/.config drift → inject additionalContext to re-read |
| utils.py | (shared library) | read_event(), get_cwd(), parse_roadmap_now(), parse_roadmap_section(), project_tmp_path(), call_zie_memory_api(), safe_write_tmp() (symlink-safe, atomic write) |

## Agents

| Agent | Model | Memory | Invoked by |
| --- | --- | --- | --- |
| spec-reviewer | haiku | project | skills/spec-design (Step 5) |
| plan-reviewer | haiku | project | commands/zie-plan (plan-reviewer gate) |
| impl-reviewer | haiku | project | commands/zie-implement (Step 6) |
