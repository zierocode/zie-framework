# Plan: zie-init — Generate CLAUDE.md + Seed zie-memory

**Spec**: specs/zie-init-claude-md-memory.md
**Date**: 2026-03-22
**Status**: in progress

---

## Tasks

- [x] T1: Create `templates/CLAUDE.md.template` with correct placeholders
- [x] T2: Fix `commands/zie-init.md` — remove wrong step 8 (local ~/.claude path), update step 9 (richer zie-memory context)
- [x] T3: Write pytest tests covering acceptance criteria 1–4 (9 tests)
- [x] T4: Make tests pass (GREEN) — 9/9 passed

---

## Notes

- T1 already done (2026-03-22) but without spec/plan — treating as complete
- T2 is a fix: step 8 currently references local `~/.claude/projects` path — wrong, must remove
- Tests live in `tests/unit/test_zie_init_templates.py`
- Test runner: pytest (`make test-unit`)
