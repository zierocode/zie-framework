---
approved: true
approved_at: 2026-04-04
backlog: backlog/fix-retro-roadmap-redundant-reads.md
---

# Fix Retro ROADMAP Redundant Reads — Implementation Plan

**Goal:** Eliminate two redundant `ROADMAP.md` reads in `/retro` by threading a single `roadmap_raw` binding from pre-flight through Done-write and Done-rotation sections.
**Architecture:** Pure command markdown edit — bind `roadmap_raw` at pre-flight step 3, reference it by name in downstream sections instead of issuing new Read calls. No Python changes needed.
**Tech Stack:** Markdown (commands/retro.md), pytest (structural assertion tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/retro.md` | Thread `roadmap_raw` binding; remove two downstream reads |
| Modify | `tests/unit/test_retro_lean_context.py` | Assert `roadmap_raw` bound at pre-flight; assert downstream sections reference it |

---

## Task 1: Bind `roadmap_raw` at pre-flight step 3

**Acceptance Criteria:**
- Pre-flight step 3 explicitly names the cached variable `roadmap_raw` (full ROADMAP content)
- Instruction text makes clear that `roadmap_raw` is available to all downstream steps

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing test (RED)**
  ```python
  # tests/unit/test_retro_roadmap_single_read.py
  from pathlib import Path
  CMD = Path(__file__).parents[2] / "commands" / "retro.md"

  class TestRoadmapSingleRead:
      def test_preflight_binds_roadmap_raw(self):
          src = CMD.read_text()
          assert "roadmap_raw" in src, \
              "Pre-flight must bind roadmap_raw variable"

      def test_roadmap_raw_defined_before_steps(self):
          src = CMD.read_text()
          preflight_end = src.find("## Steps")
          raw_pos = src.find("roadmap_raw")
          assert raw_pos != -1, "roadmap_raw must be defined"
          assert raw_pos < preflight_end, \
              "roadmap_raw must be bound before ## Steps section"
  ```
  Run: `make test-unit` — must FAIL (roadmap_raw not yet in retro.md)

- [ ] **Step 2: Implement (GREEN)**
  Edit `commands/retro.md` pre-flight step 3, change:
  ```
  3. Targeted ROADMAP reads: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines only. Grep `## Next` → read to next `---` (cache as `next_lane` — reused by Suggest next, no second read).
  ```
  To:
  ```
  3. Read `zie-framework/ROADMAP.md` → bind as `roadmap_raw` (reused by all downstream sections — no second read). Extract: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines only (bind as `done_section_raw`). Grep `## Next` → read to next `---` (cache as `next_lane`).
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify wording is clear and consistent. No further changes needed.
  Run: `make test-unit` — still PASS

---

## Task 2: Remove redundant read in "Update ROADMAP Done inline"

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- "Update ROADMAP Done inline" section no longer instructs a `Read` of ROADMAP.md
- Section references `roadmap_raw` as its starting content
- Test enforces no re-read instruction in that section

**Files:**
- Modify: `commands/retro.md`
- Modify: `tests/unit/test_retro_roadmap_single_read.py`

- [ ] **Step 1: Write failing test (RED)**
  Add to `tests/unit/test_retro_roadmap_single_read.py`:
  ```python
  def test_done_write_uses_roadmap_raw(self):
      src = CMD.read_text()
      # Find the Update ROADMAP Done inline section
      section_start = src.find("Update ROADMAP Done inline")
      assert section_start != -1, "Update ROADMAP Done inline section must exist"
      next_section = src.find("\n###", section_start + 1)
      section = src[section_start:next_section] if next_section != -1 else src[section_start:]
      # Must NOT have a bare "Read `zie-framework/ROADMAP.md`" instruction
      assert "Read `zie-framework/ROADMAP.md`" not in section, \
          "Done-write section must not re-read ROADMAP.md — use roadmap_raw"
      # Must reference roadmap_raw
      assert "roadmap_raw" in section, \
          "Done-write section must use roadmap_raw binding"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  Edit `commands/retro.md` "Update ROADMAP Done inline" section, change:
  ```
  **Update ROADMAP Done inline.**
  - Read `zie-framework/ROADMAP.md`.
  - Move shipped items from `shipped_items` to the `## Done` section with date and version tag.
  ```
  To:
  ```
  **Update ROADMAP Done inline.**
  - Use `roadmap_raw` (bound at pre-flight — no re-read needed).
  - Move shipped items from `shipped_items` to the `## Done` section with date and version tag.
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No structural changes needed.
  Run: `make test-unit` — still PASS

---

## Task 3: Remove redundant read in "Done-rotation"

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- "Done-rotation" section no longer instructs a `Read` of ROADMAP.md
- Section references `roadmap_raw` (or updated content from Task 2) as its source
- Test enforces no re-read instruction in Done-rotation section

**Files:**
- Modify: `commands/retro.md`
- Modify: `tests/unit/test_retro_roadmap_single_read.py`

- [ ] **Step 1: Write failing test (RED)**
  Add to `tests/unit/test_retro_roadmap_single_read.py`:
  ```python
  def test_done_rotation_uses_roadmap_raw(self):
      src = CMD.read_text()
      rotation_start = src.find("Done-rotation (inline)")
      assert rotation_start != -1, "Done-rotation section must exist"
      next_section = src.find("\n###", rotation_start + 1)
      section = src[rotation_start:next_section] if next_section != -1 else src[rotation_start:]
      # Must NOT have a bare "Read `## Done` from `zie-framework/ROADMAP.md`" instruction
      assert "Read `## Done` from `zie-framework/ROADMAP.md`" not in section, \
          "Done-rotation must not re-read ROADMAP.md — use roadmap_raw"
      # Must reference roadmap_raw
      assert "roadmap_raw" in section, \
          "Done-rotation must use roadmap_raw binding"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  Edit `commands/retro.md` "Done-rotation" section, change:
  ```
  1. Read `## Done` from `zie-framework/ROADMAP.md`. ≤ 10 items → skip entirely.
  ```
  To:
  ```
  1. Parse `## Done` from `roadmap_raw` (already bound at pre-flight — no re-read). ≤ 10 items → skip entirely.
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Run full suite to confirm no regressions.
  Run: `make test-unit` — still PASS

---

## Task 4: Assert single-read contract in test suite

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- Test file `test_retro_roadmap_single_read.py` fully covers all three assertions (pre-flight bind, done-write no re-read, done-rotation no re-read)
- All existing retro tests still pass (`make test-unit`)

**Files:**
- Modify: `tests/unit/test_retro_roadmap_single_read.py`

- [ ] **Step 1: Write failing test (RED)**
  Add integration-style assertion:
  ```python
  def test_roadmap_read_count(self):
      """ROADMAP.md must appear as a Read target at most once (pre-flight only)."""
      import re
      src = CMD.read_text()
      # Count explicit Read instructions for ROADMAP.md
      read_patterns = re.findall(r"Read `zie-framework/ROADMAP\.md`", src)
      assert len(read_patterns) == 0, \
          f"ROADMAP.md must not appear as explicit Read target after pre-flight refactor; found {len(read_patterns)} occurrence(s)"
  ```
  Run: `make test-unit` — must FAIL if any stale read instructions remain

- [ ] **Step 2: Implement (GREEN)**
  Verify all three downstream sections are clean (Tasks 1-3 complete).
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Run full suite.
  Run: `make test-ci` — must PASS with no regressions

---

## Summary

| Task | File | Tests |
| --- | --- | --- |
| 1: Bind roadmap_raw at pre-flight | `commands/retro.md` | `test_preflight_binds_roadmap_raw`, `test_roadmap_raw_defined_before_steps` |
| 2: Remove Done-write re-read | `commands/retro.md` | `test_done_write_uses_roadmap_raw` |
| 3: Remove Done-rotation re-read | `commands/retro.md` | `test_done_rotation_uses_roadmap_raw` |
| 4: Single-read contract assertion | `tests/unit/test_retro_roadmap_single_read.py` | `test_roadmap_read_count` |

**Total tasks: 4 (S plan — single session)**
**Parallelism: none (linear dependency chain — each task builds on the previous)**
