# zie-framework

AI-native SDLC framework plugin for Claude Code. ติดตั้ง structured development
workflow เข้าไปในทุก project: spec-first TDD, intent detection, memory
integration, safety guardrails.

**Version**: 1.30.0  **Status**: active

---

## Commands

| Command | Description |
| --- | --- |
| /backlog | Capture new backlog item (problem + motivation) |
| /spec | Backlog item → design spec with reviewer loop |
| /plan | Approved spec → draft plan → approval → Ready lane |
| /implement | Ready → TDD implementation + impl-reviewer gate |
| /fix | Bug → regression test → fix → verify. Non-urgent bugs; no immediate release. |
| /release | Release gate → readiness check → `make release` → retro |
| /status | Snapshot สถานะปัจจุบัน |
| /resync | Rescan codebase + update knowledge docs + hash |
| /retro | Retrospective → ADRs → brain storage |
| /audit | 9-dimension audit + external research → scored report → backlog |
| /sprint | Sprint clear — batch all items through full pipeline (spec→plan→implement→release→retro) |
| /chore | Maintenance task track — no spec required |
| /hotfix | Emergency fix track — prod incidents only; triggers immediate release. Use /fix for non-urgent bugs. |
| /spike | Time-boxed exploration in an isolated sandbox directory |
| /next | Rank backlog items by impact, age, and dependencies — recommend top 3 |
| /rescue | Pipeline diagnosis — stuck items + recovery actions |
| /health | Hook health + config validation check |
| /guide | On-demand framework walkthrough + pipeline position |
| /brief | Display `.zie/handoff.md` session brief |
| /init | Bootstrap: initialize framework in a new project |

## Skills

> Invoked automatically by commands as subagents — not called directly by users.

| Skill | Purpose |
| --- | --- |
| spec-design | Draft design spec from backlog item |
| spec-reviewer | Review spec for completeness and correctness |
| write-plan | Convert approved spec into implementation plan |
| plan-reviewer | Review plan for feasibility and test coverage |
| tdd-loop | RED/GREEN/REFACTOR loop for a single task |
| impl-reviewer | Review implementation against spec and plan |
| verify | Post-implementation verification gate |
| test-pyramid | Test strategy advisor |
| debug | Systematic bug diagnosis and fix path |
| zie-audit | 9-dimension audit analysis (invoked by /audit command) |
| docs-sync-check | Verify CLAUDE.md and README.md are in sync with repo state |
| load-context | Load shared context bundle (ADRs + project context) for reviewer skills |
| brainstorm | Discovery skill — read project context, research, generate ideas |
| using-zie-framework | Command map, workflow map, and anti-patterns reference |

## Agents

> Session-wide agent personas — invoked via `--agent zie-framework:<name>`.

| Agent | permissionMode | Purpose |
| --- | --- | --- |
| zie-implement-mode | acceptEdits | TDD session — SDLC context, WIP=1, full tool access |
| zie-audit-mode | plan | Read-only analysis — findings surfaced as backlog candidates |

## Knowledge

- [Architecture](project/architecture.md) — system design, component
  relationships
- [Components](project/components.md) — command/skill/hook registry
- [Context](project/context.md) — design context, constraints,
  key decisions found in codebase
- [ADRs](decisions/) — formal Architecture Decision Records

## Links

- [ROADMAP](ROADMAP.md) — current backlog + active work
- [Specs](specs/) — feature designs
- [Plans](plans/) — implementation plans
