---
approved: true
approved_at: 2026-04-13
backlog: backlog/intent-sdlc-context-dedup.md
spec: specs/2026-04-13-intent-sdlc-context-dedup-design.md
---

# intent-sdlc: Deduplicate Same-Context Injection — Implementation Plan

**Goal:** Add a module-level in-process dedup cache to `hooks/intent-sdlc.py` so the hook exits 0 without output when the SDLC context hasn't changed since the last emission in this session.

**Tech Stack:** Python 3.x (no new deps), pytest (existing suite must stay green)

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `hooks/intent-sdlc.py` | Add `_last_context_key` dict; insert dedup check before emit |
| Modify | `tests/unit/test_intent_sdlc.py` | Add dedup behavior tests |

---

## Task 1 — Add `_last_context_key` module-level cache to intent-sdlc.py

**RED:** Write a test that:
- Calls the hook twice with the same session_id, same intent_cmd, stage, active_task
- Asserts second call produces no stdout output

**File:** `tests/unit/test_intent_sdlc.py`

**GREEN:** In `hooks/intent-sdlc.py`:
1. After the `COMPILED_PATTERNS` module-level block, add: `_last_context_key: dict[str, str] = {}`
2. Compute dedup key just before any `print(json.dumps(...))` call:
   ```python
   _dedup_key = f"{intent_cmd}|{stage}|{active_task[:40]}"
   if _last_context_key.get(session_id) == _dedup_key:
       sys.exit(0)
   ```
3. After each `print(json.dumps(...))` call: `_last_context_key[session_id] = _dedup_key`
4. Apply to ALL emit paths in the hook (there are 2-3 emission points — find with grep)

**Acceptance Criteria:**
- [ ] Same context → second call exits 0 with no stdout
- [ ] Different stage → re-emits normally
- [ ] Cache is module-level dict, no disk writes

---

## Task 2 — Test: dedup skips on unchanged context

**RED:** Add test verifying:
- Hook emits on first call with context X
- Hook emits nothing on second call with same context X
- Hook re-emits on third call with context Y (different stage)

**GREEN:** Tests pass via Task 1 implementation

**Acceptance Criteria:**
- [ ] New test `test_dedup_skips_repeated_context` passes
- [ ] Existing test suite still passes (2535 tests green)

---

## Estimated Risk: LOW
- In-process dict; no external dependencies, no disk I/O
- Pure additive change to emit logic
- Hook always exits 0 on exception (graceful degradation preserved)
