# Lean Load-Context — Eliminate Triple Invocation in Sprint→Implement Chain — Design Spec

**Problem:** When `/sprint` calls `/implement` via `Skill()`, the inner `implement` command re-invokes `load-context` even though `sprint` already loaded it; `spec-reviewer` and `plan-reviewer` each also invoke `reviewer-context` (their Phase 1) even when `context_bundle` is already provided by the caller — resulting in up to 3 redundant context-load invocations per sprint cycle.

**Approach:** Enforce the existing fast-path contracts already documented in `load-context/SKILL.md` and `reviewer-context/SKILL.md`. The fast-path logic already exists ("if `context_bundle` provided → skip disk reads") but is never triggered because callers don't pass `context_bundle` through the chain. The fix is prose-only: update `sprint.md` (Phase 3) to pass `context_bundle` when invoking `zie-implement`, update `implement.md` to pass `context_bundle` when invoking `impl-reviewer`, and tighten the reviewer fast-path contract wording so the guard is unambiguous. No new mechanisms required.

**Components:**
- `commands/sprint.md` — Phase 3 `Skill(zie-framework:zie-implement, <slug>)` call: add `context_bundle` as argument
- `commands/implement.md` — `impl-reviewer` dispatch: confirm `context_bundle` is passed (already documented; verify wording is explicit)
- `skills/reviewer-context/SKILL.md` — fast-path guard: strengthen "if `context_bundle` provided → return immediately, skip all disk reads"
- `skills/load-context/SKILL.md` — add fast-path guard: "if `context_bundle` already provided as argument → return it immediately, skip all steps"
- `tests/unit/test_lean_load_context.py` — new structural tests verifying pass-through wording exists in each file

**Data Flow:**
1. `/sprint` invokes `Skill(zie-framework:load-context)` → binds `context_bundle`
2. Sprint Phase 1 already passes `context_bundle` to each parallel spec+plan agent (existing behavior preserved)
3. Sprint Phase 3: `Skill(zie-framework:zie-implement, <slug>, context_bundle=<context_bundle>)` — NEW: `context_bundle` passed explicitly
4. `/implement` receives `context_bundle` → fast-paths its own `load-context` call (returns immediately, no disk read)
5. `/implement` dispatches `@agent-impl-reviewer` with `context_bundle` (already documented, verify is explicit)
6. `impl-reviewer` → `reviewer-context` fast-path: `context_bundle` present → skip ADR + `context.md` disk reads, return `adrs_content` + `context_content` immediately
7. `spec-reviewer` and `plan-reviewer` (invoked in Phase 1 agents): already receive `context_bundle` from Phase 1 agent prompt — verify fast-path wording in `reviewer-context` is unconditional

**Edge Cases:**
- `context_bundle` is `None` or absent (e.g., direct `/implement` call outside sprint) → existing disk-read fallback path remains unchanged; no regression
- `context_bundle` passed but `adrs` key is empty string → fast-path still triggers; reviewer treats empty ADRs as "No ADRs found" (existing behavior)
- Sprint Phase 2 (`/plan` multi-slug invocation) already operates independently and loads its own context bundle; not in scope for this change
- `reviewer-context` called by `spec-reviewer` or `plan-reviewer` outside sprint (direct `/spec` or `/plan` call) → `context_bundle` absent → falls through to disk path normally

**Out of Scope:**
- Modifying the `load-context` caching mechanism (ADR-031 / `write_adr_cache`) — cache layer stays
- Changing how Phase 1 parallel spec agents receive `context_bundle` (already passing it)
- Changing `/plan` command's load-context invocation (not part of the sprint→implement chain being fixed)
- Python hook changes — prose-only fix
- E2E or integration tests — structural (markdown text) tests only
