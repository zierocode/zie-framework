# Plan: docs-sync-consolidate

**status:** approved
**spec:** zie-framework/specs/2026-04-04-docs-sync-consolidate-design.md
**date:** 2026-04-04

---

## Tasks

### Task 1 — Re-activate `skills/docs-sync-check/SKILL.md`

- Remove `deprecated: true`, `deprecated_since`, and `deprecated_reason` frontmatter fields.
- Remove the `> **DEPRECATED** ...` banner block from the skill body.
- Restore the description line: `description: Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk. Returns JSON verdict.`
- Confirm Steps 3 in the skill body enumerates all three: commands (`commands/*.md`), skills (`skills/*/SKILL.md`), hooks (`hooks/*.py` excluding `utils.py`). No content change needed — coverage is already present.

### Task 2 — Update `commands/zie-retro.md`

- Remove lines 66–81 (the "Check docs sync inline" block): the skip guard, the 7-step enumeration, and the verdict print logic.
- Replace with:
  ```
  2. **Check docs sync.**
     Invoke `Skill(zie-framework:docs-sync-check)`. Print the returned `details` string as the verdict.
     Skip guard: if `git log -1 --format="%s"` starts with `release:` → print `"Docs-sync: skipped (ran during release)"` and skip.
  ```
- Verify the surrounding context (section numbering, "รวมผลลัพธ์" section) remains correct after the replacement.

### Task 3 — Update `commands/zie-release.md`

- Remove the Pre-Gate-1 Bash snippet (the `python3 -c "..."` block, lines ~31–48).
- Replace with:
  ```
  Run docs-sync check before unit tests — invoke `Skill(zie-framework:docs-sync-check)` (run_in_background=True if supported).
  Fallback: if Skill unavailable → print `[zie-framework] docs-sync-check unavailable — skipping`. Manual check: `make docs-sync`
  ```
- Keep the Collect Parallel Gate Results section's docs-sync handling text intact (lines ~113–116 — already references `docs-sync-check unavailable` and `make docs-sync`).
- Verify `CLAUDE.md` and `README.md` are still mentioned in the file (they appear in the collect-results block; confirm this is sufficient for the test or update the block to reference the skill instead).

### Task 4 — Update `tests/unit/test_docs_sync_check_general_agent.py`

Update four test methods to match the new consolidation:

1. **`test_release_uses_inline_bash_for_docs_sync`**: Change assertion to accept `Skill(zie-framework:docs-sync-check)` as the mechanism (drop `python3 -c` requirement). Remove `assert "Agent(" not in text` if Skill invocation uses that internally — or keep it if Skill() syntax does not trigger it.

2. **`test_retro_uses_general_purpose_for_docs_sync`**: Replace `assert "general-purpose" in text` with `assert "Skill(zie-framework:docs-sync-check)" in text`.

3. **`test_docs_sync_inline_instructions_in_release`**: Relax to check that either the inline text or the skill name references the intent. Simplest: assert `"docs-sync-check" in text` (already true via fallback text).

4. **`test_docs_sync_inline_instructions_in_retro`**: Same relaxation — assert `"docs-sync-check" in text` or `"Skill(zie-framework:docs-sync-check)" in text`.

### Task 5 — Verify full test suite

```bash
make test-fast
```

Expected: all tests green. If any assertion failures remain, fix the specific assertion — do not change behavior in command files.

---

## Files to Change

| File | Change |
|------|--------|
| `skills/docs-sync-check/SKILL.md` | Remove deprecated flags and banner |
| `commands/zie-retro.md` | Replace inline docs-sync block (~16 lines) with Skill() invocation |
| `commands/zie-release.md` | Replace Pre-Gate-1 Bash snippet with Skill() invocation; preserve fallback text |
| `tests/unit/test_docs_sync_check_general_agent.py` | Update 4 test assertions to match Skill()-based approach |

**Files that must NOT change:**
- `tests/unit/test_release_lean_fallback.py` — all 3 assertions must continue to pass naturally
- `tests/unit/test_model_effort_frontmatter.py` — skill file still exists with haiku/low, no change needed
- `tests/unit/test_hybrid_release.py` — `test_zie_release_no_blocking_docs_sync_fallback` checks for absence of a specific string we are not adding
- `Makefile` — `docs-sync:` target stays as-is

---

## Order of Operations

1. Task 1 (skill) — unblocks accurate behavior description
2. Task 2 (retro) — removes inline prose
3. Task 3 (release) — removes Bash snippet
4. Task 4 (tests) — update assertions to match new reality
5. Task 5 (verify) — confirm green
