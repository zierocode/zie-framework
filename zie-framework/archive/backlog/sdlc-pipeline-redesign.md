ทด# SDLC Pipeline Redesign — 6-Stage Standard Pipeline

## Problem

zie-framework commands ไม่ align กับ 5-stage SDLC standard:

1. `/zie-idea` ทำหน้าที่หลายอย่างในคำสั่งเดียว (brainstorm + spec + plan +
   backlog) ทำให้ยากต่อการเข้าใจว่าแต่ละ command ทำอะไร
2. `/zie-build` และ `/zie-ship` ชื่อไม่ตรงกับ stage ที่มันทำ
3. ไม่มี quality gate (reviewer loop) ที่ stage 2, 3, 4 — เฉพาะ stage 5
   ที่มี test gates

## Target: 6-Stage Pipeline

```
idea → [zie-backlog]   → backlog/<slug>.md
     → [zie-spec]      → specs/YYYY-MM-DD-<slug>-design.md  → [spec-reviewer] ✅
     → [zie-plan]      → plans/YYYY-MM-DD-<slug>.md          → [plan-reviewer] ✅
     → [zie-implement] → working code                         → [impl-reviewer] ✅
     → [zie-release]   → tagged release                       → [test gates]    ✅
     → [zie-retro]     → decisions/<slug>-adr.md
```

## Stage ใหม่ + Quality Gates

### Stage 1: `zie-backlog` — Capture idea

- **Input:** idea จาก user (text หรือ argument)
- **Output:** `zie-framework/backlog/<slug>.md` (problem, motivation, rough
  scope)
- **ROADMAP lane:** Next
- **Quality gate:** ไม่มี

### Stage 2: `zie-spec` — Backlog → Spec

- **Input:** `backlog/<slug>.md`
- **Output:** `specs/YYYY-MM-DD-<slug>-design.md` พร้อม Acceptance Criteria
- **ROADMAP lane:** Next → Spec (ถ้าเพิ่ม lane) หรือ Next (ถ้าใช้ flag)
- **Quality gate:** spec-reviewer subagent loop
  - ตรวจ: ความครบถ้วน, AC ชัดเจน, ไม่มี ambiguity, feasible
  - วน loop จนผ่าน (max 3 iterations → surface to human)

### Stage 3: `zie-plan` — Spec → Implementation Plan

- **Input:** approved spec
- **Output:** `plans/YYYY-MM-DD-<slug>.md` พร้อม `approved: true`
- **ROADMAP lane:** Next → Ready
- **Quality gate:** plan-reviewer subagent loop
  - ตรวจ: AC ทุกข้อมี task, TDD structure, estimate สมเหตุสมผล
  - วน loop จนผ่าน (max 3 iterations → surface to human)

### Stage 4: `zie-implement` — Plan → Working Code

- **Input:** approved plan (Ready lane)
- **Output:** committed, tested code
- **ROADMAP lane:** Ready → Now → (stays in Now until release)
- **Per-task flow:** RED → GREEN → REFACTOR → commit
- **Quality gate:** impl-reviewer subagent หลังทุก task
  - ตรวจ: AC met, no bugs, code quality, optimization
  - วน loop จนผ่าน

### Stage 5: `zie-release` — Code → Release

- **Input:** passing tests + approved code
- **Output:** tagged release on main + CHANGELOG
- **ROADMAP lane:** Now → Done
- **Quality gate (existing):** unit + int + e2e + docs sync + code diff

### Stage 6: `zie-retro` — Learnings

- **Input:** shipped release
- **Output:** ADRs ใน `decisions/`, ROADMAP "Done" updated
- **Quality gate:** ไม่มี

---

## Impact Analysis — ไฟล์ที่ต้องเปลี่ยน

### Commands (8 files)

| File | Action | Detail |
| --- | --- | --- |
| `commands/zie-idea.md` | Split → 2 files | → `zie-backlog.md` + `zie-spec.md` |
| `commands/zie-build.md` | Rename | → `zie-implement.md` |
| `commands/zie-ship.md` | Rename | → `zie-release.md` |
| `commands/zie-plan.md` | Update | input = approved spec (ไม่ใช่ raw backlog) |
| `commands/zie-fix.md` | No change | — |
| `commands/zie-retro.md` | No change | — |
| `commands/zie-status.md` | No change | — |
| `commands/zie-init.md` | No change | — |

### Skills (6 updates + 3 new)

| File | Action | Detail |
| --- | --- | --- |
| `skills/spec-design/SKILL.md` | Update | invoke spec-reviewer loop หลัง draft |
| `skills/write-plan/SKILL.md` | Update | invoke plan-reviewer loop หลัง draft |
| `skills/tdd-loop/SKILL.md` | Update | reference zie-implement แทน zie-build |
| `skills/verify/SKILL.md` | Update | reference zie-release แทน zie-ship |
| `skills/retro-format/SKILL.md` | Update | reference updates |
| `skills/test-pyramid/SKILL.md` | Update | reference updates |
| `skills/spec-reviewer/SKILL.md` | **Create** | subagent prompt สำหรับ spec review |
| `skills/plan-reviewer/SKILL.md` | **Create** | subagent prompt สำหรับ plan review |
| `skills/impl-reviewer/SKILL.md` | **Create** | subagent prompt: AC, bugs, quality, |
| | | optimization |

### Hooks (2 files)

| File | Line | Change |
| --- | --- | --- |
| `hooks/intent-detect.py` | PATTERNS | rename "idea"→"backlog"+"spec", |
| | | "build"→"implement", "ship"→"release" |
| `hooks/intent-detect.py` | SUGGESTIONS | update mapping ให้ตรงกับชื่อใหม่ |
| `hooks/session-resume.py` | line 85 | "run /zie-idea" → "run /zie-backlog" |
| `hooks/session-resume.py` | line 69 | ลบ superpowers_enabled reference |

### Tests (6 files)

| File | Scope of change |
| --- | --- |
| `tests/unit/test_hooks_intent_detect.py` | assertions เปลี่ยนตาม command ใหม่ |
| `tests/unit/test_e2e_optimization.py` | file paths + assertions (14+ จุด) |
| `tests/unit/test_branding.py` | zie-build / zie-ship → ชื่อใหม่ |
| `tests/unit/test_sdlc_gates.py` | zie-ship / zie-build / zie-idea assertions |
| `tests/unit/test_hooks_session_resume.py` | "/zie-idea" assertion |
| `tests/unit/test_fork_superpowers_skills.py` | old command name references |

### Documentation (6 files)

| File | Change |
| --- | --- |
| `CLAUDE.md` | command references ในส่วน Development Commands |
| `README.md` | command list + description table |
| `zie-framework/PROJECT.md` | architecture overview, command flow |
| `zie-framework/project/architecture.md` | command flow diagram |
| `zie-framework/project/components.md` | component descriptions |
| `zie-framework/project/decisions.md` | decision history references |

### Plugin Metadata (1 file)

| File | Change |
| --- | --- |
| `.claude-plugin/marketplace.json` | description: old command list → new |

### ROADMAP.md (meta + structure)

- Line 4: "Updated by /zie-idea (Next), /zie-plan (Ready), /zie-build (Now),
  /zie-ship (Done)" → ชื่อใหม่
- พิจารณาเพิ่ม lane **Spec** ระหว่าง Next และ Ready:
  - **Next** → raw backlog (จาก zie-backlog)
  - **Spec** → มี approved spec รออยู่ (จาก zie-spec)
  - **Ready** → มี approved plan (จาก zie-plan)
  - **Now** → กำลัง implement (จาก zie-implement)
  - **Done** → shipped

### ไม่ต้องเปลี่ยน (historical record)

- `zie-framework/plans/*.md` — historical plans
- `zie-framework/specs/*.md` — historical specs
- `CHANGELOG.md` — release history
- Folder structure — align อยู่แล้ว

---

## Folder Structure (ไม่เปลี่ยน — align แล้ว)

```text
zie-framework/
├── backlog/      ← Stage 1 output (zie-backlog)
├── specs/        ← Stage 2 output (zie-spec)
├── plans/        ← Stage 3 output (zie-plan)
├── decisions/    ← Stage 6 output (zie-retro ADRs)
├── evidence/     ← Stage 4 reviewer artifacts (gitignored)
└── project/      ← knowledge hub (architecture, components)
```

---

## Out of Scope

- เปลี่ยน `/zie-init` behavior
- เปลี่ยน `/zie-fix` flow
- เปลี่ยน hook system architecture
- เปลี่ยน historical plans/specs filenames
