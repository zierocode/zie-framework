# Components Registry — zie-framework

**Last updated:** 2026-03-22

## Commands

| Command | Input | Output | Dependencies |
|---|---|---|---|
| /zie-idea | idea (optional) | spec + backlog item | spec-design skill |
| /zie-plan | slug(s) | approved plan in Ready | write-plan skill |
| /zie-build | (reads ROADMAP Now) | implemented feature | tdd-loop, test-pyramid, debug skills |
| /zie-fix | bug description | regression test + fix | debug, verify skills |
| /zie-ship | (reads ROADMAP Now) | release tag + ADRs | verify skill |
| /zie-status | (reads files) | status snapshot | none |
| /zie-retro | (reads git log) | ADRs + brain memories | retro-format skill |

## Skills

| Skill | ทำอะไร | Invoked by |
|---|---|---|
| spec-design | Brainstorm → design spec | /zie-idea |
| write-plan | Spec → task plan | /zie-idea, /zie-plan |
| tdd-loop | RED/GREEN/REFACTOR guide | /zie-build |
| test-pyramid | Choose test level (unit/int/e2e) | /zie-build (RED phase) |
| debug | Reproduce → isolate → fix | /zie-build, /zie-fix |
| verify | Pre-ship verification checklist | /zie-fix, /zie-ship |
| retro-format | ADR + retro structure | /zie-retro |

## Hooks

| Hook | Event | ทำอะไร |
|---|---|---|
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save (debounced) |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous commands (rm -rf /, sudo) |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent จาก bash pattern → suggest /zie-* command |
| session-resume.py | SessionStart | แสดง project state + active feature |
| session-learn.py | PostToolUse | สังเกต patterns และบันทึก micro-learnings |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP progress สู่ brain |
