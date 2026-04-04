---
approved: true
approved_at: 2026-04-04
backlog: backlog/align-load-context-adr-cache-protocol.md
---

# Align load-context ADR Cache Protocol — Implementation Plan

**Goal:** Prepend a `get_cached_adrs` cache-check step to `load-context` SKILL.md so it matches the cache-first protocol already used by `reviewer-context`.
**Architecture:** Single skill file edit — `skills/load-context/SKILL.md` gains a Step 0 cache-check before the existing disk-read loop. Cache hit skips disk reads; cache miss falls through to existing logic. The `context_bundle` output contract remains unchanged.
**Tech Stack:** Markdown skill definitions only — no Python changes required.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/load-context/SKILL.md` | Prepend Step 0 cache-check; restructure steps to numbered 0–4 |
| Modify | `tests/unit/test_reviewer_skill_adr_cache.py` | Add `load-context` cache-hit assertions |

---

## Task 1: Update load-context SKILL.md with cache-first protocol

**Acceptance Criteria:**
- `skills/load-context/SKILL.md` contains a Step 0 that calls `get_cached_adrs(session_id, "zie-framework/decisions/")` before any disk reads.
- Cache hit path is documented: skip disk-read loop, use cached `adrs_content` directly.
- Cache miss path falls through to existing Step 1 (read all `decisions/*.md` from disk).
- `write_adr_cache` call is retained in the cache-miss path.
- `context_bundle` output contract is unchanged.

**Files:**
- Modify: `skills/load-context/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_reviewer_skill_adr_cache.py`:

  ```python
  def test_load_context_references_get_cached_adrs():
      assert "get_cached_adrs" in _skill_text("load-context")


  def test_load_context_references_write_adr_cache():
      assert "write_adr_cache" in _skill_text("load-context")


  def test_load_context_has_cache_miss_fallback():
      text = _skill_text("load-context")
      assert "Cache miss" in text or "cache miss" in text


  def test_load_context_has_cache_hit_skip():
      text = _skill_text("load-context")
      assert "Cache hit" in text or "cache hit" in text
  ```

  Run: `make test-unit` — must FAIL (load-context currently has no `get_cached_adrs` reference)

- [ ] **Step 2: Implement (GREEN)**

  Replace `skills/load-context/SKILL.md` Steps section with:

  ```markdown
  ## Steps

  **Step 0: Cache check**
  - Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
    - Cache hit → `adrs_content` ← returned value; skip Step 1.
    - Cache miss → proceed to Step 1.

  **Step 1: ADRs (disk fallback — cache miss only)**
  - Read all `zie-framework/decisions/*.md` → concatenate →
    `adrs_content` (empty string if directory missing or empty).

  **Step 2: Cache write**
  - Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
    - Returns `(True, adr_cache_path)` → save path
    - Returns `(False, None)` → set `adr_cache_path = None`

  **Step 3: Design context**
  - Read `zie-framework/project/context.md` →
    `context_content` (empty string if file missing).

  **Step 4: Assemble bundle**
  - Build and return:
    ```
    context_bundle = {
      adr_cache_path: <path or None>,
      adrs: adrs_content,
      context: context_content
    }
    ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify `skills/load-context/SKILL.md` header metadata (`name`, `description`, `allowed-tools`, etc.) is unchanged.
  - Verify `context_bundle` output section remains intact and unchanged.
  - Run: `make test-unit` — still PASS

---

## Task 2: Update test coverage for load-context cache protocol

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `test_reviewer_skill_adr_cache.py` includes cache assertions for `load-context` (not just the three reviewer skills).
- Tests cover both `get_cached_adrs` and `write_adr_cache` references in `load-context`.
- Full unit test suite still passes.

**Files:**
- Modify: `tests/unit/test_reviewer_skill_adr_cache.py`

- [ ] **Step 1: Write failing tests (RED)**

  (Already written in Task 1, Step 1 — tests fail until Task 1 is complete.)

  Verify tests still fail before Task 1 changes are applied:
  Run: `make test-unit` — `test_load_context_references_get_cached_adrs` FAIL expected

- [ ] **Step 2: Implement (GREEN)**

  After Task 1 edits are in place, run:
  Run: `make test-unit` — all 4 new `test_load_context_*` tests must PASS

- [ ] **Step 3: Refactor**
  - Check that existing reviewer cache tests still pass (no regressions).
  - Run: `make test-unit` — still PASS

---

## Summary

| Task | File | Size | Parallel? |
| --- | --- | --- | --- |
| Task 1 | `skills/load-context/SKILL.md` | S | Yes |
| Task 2 | `tests/unit/test_reviewer_skill_adr_cache.py` | S | No (depends Task 1) |

Total: 2 tasks — S plan (single-session).
