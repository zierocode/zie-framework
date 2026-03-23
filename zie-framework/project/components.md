# Components Registry — zie-framework

**Last updated:** 2026-03-23

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
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced) |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous cmds (exit 2 = block) |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent → suggest cmd (JSON out) |
| session-resume.py | SessionStart | แสดง project state + active feature |
| session-learn.py | PostToolUse | สังเกต patterns, บันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain |
| session-cleanup.py | Stop | ลบ project-scoped /tmp files on exit |
| utils.py | (shared library) | parse_roadmap_now() + project_tmp_path() |
