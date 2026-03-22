# zie-framework

AI-native SDLC framework plugin for Claude Code. ติดตั้ง structured development workflow เข้าไปในทุก project: spec-first TDD, intent detection, memory integration, safety guardrails.

**Version**: 1.0.0  **Status**: active

---

## Commands

| Command | ทำอะไร |
| --- | --- |
| /zie-idea | Brainstorm → spec → backlog item |
| /zie-plan | Backlog → draft plan → approval → Ready lane |
| /zie-build | Ready → TDD implementation (RED/GREEN/REFACTOR) |
| /zie-fix | Bug → regression test → fix → verify |
| /zie-ship | Release gate → merge dev→main → tag → retro |
| /zie-status | Snapshot สถานะปัจจุบัน |
| /zie-retro | Retrospective → ADRs → brain storage |

## Knowledge

- [Architecture](project/architecture.md) — system design, component relationships
- [Components](project/components.md) — command/skill/hook registry
- [Decisions](project/decisions.md) — ADR log

## Links

- [ROADMAP](ROADMAP.md) — current backlog + active work
- [Specs](specs/) — feature designs
- [Plans](plans/) — implementation plans
