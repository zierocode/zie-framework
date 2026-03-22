# zie-framework

AI-native SDLC framework plugin for Claude Code. ติดตั้ง structured development
workflow เข้าไปในทุก project: spec-first TDD, intent detection, memory
integration, safety guardrails.

**Version**: 1.2.0  **Status**: active

---

## Commands

| Command | ทำอะไร |
| --- | --- |
| /zie-backlog | Capture new backlog item (problem + motivation) |
| /zie-spec | Backlog item → design spec with reviewer loop |
| /zie-plan | Approved spec → draft plan → approval → Ready lane |
| /zie-implement | Ready → TDD implementation + impl-reviewer gate |
| /zie-fix | Bug → regression test → fix → verify |
| /zie-release | Release gate → merge dev→main → tag → retro |
| /zie-status | Snapshot สถานะปัจจุบัน |
| /zie-resync | Rescan codebase + update knowledge docs + hash |
| /zie-retro | Retrospective → ADRs → brain storage |

## Knowledge

- [Architecture](project/architecture.md) — system design, component
  relationships
- [Components](project/components.md) — command/skill/hook registry
- [Decisions](project/decisions.md) — ADR log

## Links

- [ROADMAP](ROADMAP.md) — current backlog + active work
- [Specs](specs/) — feature designs
- [Plans](plans/) — implementation plans
