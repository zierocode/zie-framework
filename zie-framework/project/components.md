# Components Registry — zie-framework

**Last updated:** 2026-03-23

## Commands

| Command | Input | Output | Dependencies |
| --- | --- | --- | --- |
| /zie-backlog | idea title (optional) | backlog item file | none |
| /zie-spec | backlog slug | approved spec | spec-design skill |
| /zie-plan | slug(s) | approved plan in Ready | write-plan skill |
| /zie-implement | (reads ROADMAP Now) | implemented feature | tdd-loop, test-pyr |
| /zie-fix | bug description | regression test + fix | debug, verify skills |
| /zie-release | (reads ROADMAP Now) | release tag + ADRs | verify skill |
| /zie-status | (reads files) | status snapshot | none |
| /zie-resync | (codebase scan) | updated knowledge docs | Agent(Explore) |
| /zie-retro | (reads git log) | ADRs + brain memories | retro-format skill |

## Skills

| Skill | ทำอะไร | Invoked by |
| --- | --- | --- |
| spec-design | Brainstorm → design spec + spec-reviewer loop | /zie-spec |
| spec-reviewer | Review spec completeness + YAGNI | spec-design |
| write-plan | Spec → task plan + plan-reviewer loop | /zie-plan, spec-design |
| plan-reviewer | Review plan TDD structure + spec coverage | write-plan |
| tdd-loop | RED/GREEN/REFACTOR guide | /zie-implement |
| impl-reviewer | Review task AC coverage + test quality | /zie-implement |
| test-pyramid | Choose test level (unit/int/e2e) | /zie-implement (RED phase) |
| debug | Reproduce → isolate → fix | /zie-implement, /zie-fix |
| verify | Pre-release verification checklist | /zie-fix, /zie-release |
| retro-format | ADR + retro structure | /zie-retro |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced) |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous commands (rm -rf /, sud |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent จาก bash pattern → suggest |
| session-resume.py | SessionStart | แสดง project state + active feature |
| session-learn.py | PostToolUse | สังเกต patterns และบันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain |
