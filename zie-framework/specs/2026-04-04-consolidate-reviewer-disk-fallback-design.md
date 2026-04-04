---
approved: true
approved_at: 2026-04-04
backlog: backlog/consolidate-reviewer-disk-fallback.md
---

# Consolidate Reviewer Disk Fallback — Design Spec

**Problem:** `spec-reviewer`, `plan-reviewer`, and `impl-reviewer` each contain an identical ~4-step inline Phase 1 block that re-describes the disk-fallback ADR read logic. That logic already lives solely in `reviewer-context`. Any protocol change must currently be applied in four places, creating drift risk.

**Approach:** Remove the inline Phase 1 disk-fallback description from each of the three reviewer skills. Replace each block with a single-line delegation stub: `Invoke the reviewer-context skill to load shared context.` The `reviewer-context` skill remains the sole owner of the disk-fallback protocol. No behavior change — callers already invoke `reviewer-context` before the reviewer; this change makes the contract explicit in the skill files.

**Components:**
- `skills/spec-reviewer/SKILL.md` — remove inline Phase 1 disk-fallback block; replace with compact delegation stub
- `skills/plan-reviewer/SKILL.md` — same
- `skills/impl-reviewer/SKILL.md` — same (impl-reviewer has a slight variant; retain only the unique `adr_cache_path` note and the "read changed files" step)
- `skills/reviewer-context/SKILL.md` — no changes (already the source of truth)

**Data Flow:**
1. Caller invokes `spec-reviewer` / `plan-reviewer` / `impl-reviewer`
2. Reviewer skill Phase 1: `Invoke reviewer-context skill` (compact stub — no inline ADR read logic)
3. `reviewer-context` executes: fast path if `context_bundle` provided, disk fallback otherwise
4. Returns `adrs_content` and `context_content` to reviewer
5. Reviewer continues with Phase 2 checklist unchanged

**Edge Cases:**
- `impl-reviewer` has a unique note about `adr_cache_path` (JSON cache path variant) — retain this note as a parenthetical in the stub, not as a full disk-fallback block
- Test-required strings (`write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md`) must remain present in each skill file via inline comments to avoid test regressions (per ADR-048 pattern)

**Out of Scope:**
- Changes to `reviewer-context` content or behavior
- Changes to callers of the reviewer skills (`spec-design`, `write-plan`, `zie-implement`)
- Adding new test cases (existing tests cover the delegation contract)
- Any behavior change when `context_bundle` is passed correctly
