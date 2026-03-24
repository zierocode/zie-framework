---
approved: false
approved_at: ~
backlog: backlog/roadmap-section-aware-reads.md
spec: specs/2026-03-24-roadmap-section-aware-reads-design.md
---

# ROADMAP.md Section-Aware Reads — Implementation Plan

**Goal:** Replace full `ROADMAP.md` reads in all six commands with targeted section reads. Each command reads only the lanes it actually needs — capping token cost at the relevant section size regardless of total file length.

**Architecture:** Each command file is a Markdown instruction document. The "read ROADMAP.md" steps are prose instructions to the LLM agent running the command. The fix is to replace generic "read ROADMAP.md" instructions with precise targeted-read instructions: either a `Grep` for the section heading + limited line window, or a `Read` with offset/limit derived from locating the `## <Section>` marker. No Python hook changes, no ROADMAP format changes.

**Tech Stack:** Markdown (command definitions), pytest + `pathlib.Path.read_text()` (test validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Replace full ROADMAP read with Now-only targeted read |
| Modify | `commands/zie-status.md` | Replace full ROADMAP read with Now section + line-count grep for Next/Done |
| Modify | `commands/zie-plan.md` | Replace full ROADMAP read with Now (WIP check) + Next (item selection) |
| Modify | `commands/zie-spec.md` | Replace full ROADMAP read with Now-only targeted read |
| Modify | `commands/zie-retro.md` | Replace full ROADMAP read with Now + Done (recent, last ~20 lines) |
| Modify | `commands/zie-release.md` | Replace full ROADMAP read with Now-only targeted read |
| Create | `tests/unit/test_roadmap_section_aware_reads.py` | Assert section-aware read instruction present; assert generic full-file read absent |

---

## Section Mapping Reference

| Command | Sections needed | Rationale |
| --- | --- | --- |
| `zie-implement` | Now only | WIP check + pull first Ready item — Done/Later irrelevant |
| `zie-status` | Now (full) + line-count grep for Next/Done | Shows counts, not content, for Next/Done |
| `zie-plan` | Now (WIP check) + Next (item selection) | Never needs Done or Later |
| `zie-spec` | Now only | WIP check only — no backlog traversal needed |
| `zie-retro` | Now + Done (recent, last ~20 lines) | Shipped items for retro context; Next/Later irrelevant |
| `zie-release` | Now only | Scans `[x]` items in Now lane; Done/Later irrelevant |

---

## Targeted Read Pattern

The standard instruction pattern for each section read:

```
Grep `## <Section>` in `zie-framework/ROADMAP.md` to locate the line number,
then Read from that line until the next `---` separator (or EOF).
```

For line-count only (zie-status Next/Done counts):

```
Grep `## Next` and `## Done` in `zie-framework/ROADMAP.md` — count matching
`- [` lines in each section without reading full section content.
```

---

## Task 1: Update `commands/zie-implement.md` — Now only

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` contains an instruction to read only the Now section of ROADMAP.md (e.g., references "Now" section with targeted grep/read language)
- Does NOT contain a bare "Read `zie-framework/ROADMAP.md`" instruction without section qualification in the ตรวจสอบก่อนเริ่ม block
- Command logic (WIP check, Ready item pull) still intact

**Files:**
- Modify: `commands/zie-implement.md`
- Create: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  def read_command(filename: str) -> str:
      return (COMMANDS_DIR / filename).read_text()


  class TestZieImplement:
      def test_now_section_read_instruction_present(self):
          text = read_command("zie-implement.md")
          assert "Now" in text, "zie-implement.md must reference Now section"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-implement.md")
          # Must not instruct a bare full-file read without section qualification
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-implement.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL (bare read instruction present in step 2)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, step 2 of ตรวจสอบก่อนเริ่ม, replace:

  Before:
  ```
  2. **ตรวจสอบ: งานที่ค้างอยู่** — อ่าน `zie-framework/ROADMAP.md` → ตรวจ Now
     lane.
  ```

  After:
  ```
  2. **ตรวจสอบ: งานที่ค้างอยู่** — Grep `## Now` in `zie-framework/ROADMAP.md`
     to locate the section; Read from that line until the next `---` separator
     (Now section only — do not read Done history or Later items). ตรวจ Now lane:
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full step 2 block to confirm WIP check bullets (`[ ]` item in Now,
  `[x]` items in Now, Now empty) are untouched and still reference "Now lane"
  correctly under the new instruction.
  Run: `make test-unit` — still PASS

---

## Task 2: Update `commands/zie-status.md` — Now + line-count grep for Next/Done

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-status.md` contains an instruction to read the Now section targeted (not full file for Now content)
- Contains a grep/count instruction for Next and Done (line counts, not full section reads)
- Does NOT instruct a bare full-file read of ROADMAP.md for the purpose of building the status table

**Files:**
- Modify: `commands/zie-status.md`
- Modify: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py — add after TestZieImplement

  class TestZieStatus:
      def test_now_section_targeted_read_present(self):
          text = read_command("zie-status.md")
          assert "Now" in text, "zie-status.md must reference Now section"

      def test_next_done_count_instruction_present(self):
          text = read_command("zie-status.md")
          # Must instruct counting Next/Done rather than loading full sections
          assert "count" in text.lower() or "grep" in text.lower(), \
              "zie-status.md must instruct grep/count for Next and Done sections"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-status.md")
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-status.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-status.md`, step 2 of Steps, replace:

  Before:
  ```
  2. **Read files**: `zie-framework/.config` (including `knowledge_hash`,
     `knowledge_synced_at`), `zie-framework/ROADMAP.md`,
     `VERSION`, specs/plans dirs เพื่อ context
  ```

  After:
  ```
  2. **Read files**: `zie-framework/.config` (including `knowledge_hash`,
     `knowledge_synced_at`), `VERSION`, specs/plans dirs เพื่อ context.
     For ROADMAP.md — use targeted reads only:
     - **Now section**: Grep `## Now` → Read from that line to next `---` separator.
     - **Next count**: Grep `- [` lines between `## Next` and next `---` → count only.
     - **Done count**: Grep `- [` lines between `## Done` and next `---` → count only.
     Do not load full Next or Done section content.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm step 3 (Find active plan) and the status table format (Now: N in
  progress, Next: N queued, Done: N shipped) still align with the updated read
  instructions. The counts come from grep results, not full section reads.
  Run: `make test-unit` — still PASS

---

## Task 3: Update `commands/zie-plan.md` — Now (WIP check) + Next (item selection)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-plan.md` reads Now section targeted for WIP check
- `commands/zie-plan.md` reads Next section targeted for item listing
- Does NOT instruct a bare full-file read of ROADMAP.md

**Files:**
- Modify: `commands/zie-plan.md`
- Modify: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py — add after TestZieStatus

  class TestZiePlan:
      def test_now_section_targeted_read_present(self):
          text = read_command("zie-plan.md")
          assert "Now" in text, "zie-plan.md must reference Now section"

      def test_next_section_targeted_read_present(self):
          text = read_command("zie-plan.md")
          assert "Next" in text, "zie-plan.md must reference Next section"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-plan.md")
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-plan.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-plan.md`, step 3 of ตรวจสอบก่อนเริ่ม, replace:

  Before:
  ```
  3. Read `zie-framework/ROADMAP.md` → check Now lane.
  ```

  After:
  ```
  3. Targeted ROADMAP reads (do not read full file):
     - **Now section**: Grep `## Now` in `zie-framework/ROADMAP.md` → Read from
       that line to next `---` separator → check for `[ ]` item (WIP check).
     - **Next section**: Grep `## Next` → Read from that line to next `---`
       separator → list items for selection.
  ```

  Also update the ไม่มี argument section step 1, which reads ROADMAP.md for
  Next items:

  Before:
  ```
  - Read `zie-framework/ROADMAP.md` → list all Next items with index numbers.
  ```

  After:
  ```
  - Read Next section of `zie-framework/ROADMAP.md` only (Grep `## Next` →
    Read to next `---`) → list all Next items with index numbers.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the WIP warn logic (`[ ]` item in Now → warn), the Next-items filter
  (approved spec check), and the "Next is empty" stop condition all still work
  correctly under the targeted-read instructions.
  Run: `make test-unit` — still PASS

---

## Task 4: Update `commands/zie-spec.md` — Now only

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-spec.md` reads Now section targeted for WIP check
- Does NOT instruct a bare full-file read of ROADMAP.md
- The "no arg" fallback (list Next items) reads Next section only, not full file

**Files:**
- Modify: `commands/zie-spec.md`
- Modify: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py — add after TestZiePlan

  class TestZieSpec:
      def test_now_section_targeted_read_present(self):
          text = read_command("zie-spec.md")
          assert "Now" in text, "zie-spec.md must reference Now section"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-spec.md")
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-spec.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-spec.md`, step 3 of ตรวจสอบก่อนเริ่ม, replace:

  Before:
  ```
  3. Read `zie-framework/ROADMAP.md` → check Now lane.
  ```

  After:
  ```
  3. Grep `## Now` in `zie-framework/ROADMAP.md` → Read from that line to next
     `---` separator (Now section only) → check for `[ ]` item (WIP check).
  ```

  Also update the "no arg" detect input mode fallback in step 1:

  Before:
  ```
  - If no arg → read ROADMAP.md Next section, list items, ask: "Which to
    spec? Enter number." → slug mode.
  ```

  After:
  ```
  - If no arg → Grep `## Next` in `zie-framework/ROADMAP.md` → Read from that
    line to next `---` separator (Next section only) → list items, ask:
    "Which to spec? Enter number." → slug mode.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm WIP warn bullets (`[ ]` item → warn, `no` → stop) and the "no arg"
  item list flow are intact and consistent with targeted-read instructions.
  Run: `make test-unit` — still PASS

---

## Task 5: Update `commands/zie-retro.md` — Now + Done (recent)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-retro.md` reads Now section targeted
- `commands/zie-retro.md` reads Done section with a recency limit (~20 lines) rather than the full section
- Does NOT instruct a bare full-file read of ROADMAP.md

**Files:**
- Modify: `commands/zie-retro.md`
- Modify: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py — add after TestZieSpec

  class TestZieRetro:
      def test_now_section_targeted_read_present(self):
          text = read_command("zie-retro.md")
          assert "Now" in text, "zie-retro.md must reference Now section"

      def test_done_section_recent_limit_present(self):
          text = read_command("zie-retro.md")
          assert "Done" in text, "zie-retro.md must reference Done section"
          # Must instruct a recency limit, not a full section read
          assert "20" in text or "recent" in text.lower(), \
              "zie-retro.md must limit Done section read to recent items"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-retro.md")
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-retro.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-retro.md`, step 3 of ตรวจสอบก่อนเริ่ม, replace:

  Before:
  ```
  3. Read `zie-framework/ROADMAP.md` → current state.
  ```

  After:
  ```
  3. Targeted ROADMAP reads (do not read full file):
     - **Now section**: Grep `## Now` in `zie-framework/ROADMAP.md` → Read from
       that line to next `---` separator.
     - **Done section (recent)**: Grep `## Done` → Read from that line, limit
       to ~20 lines (recent shipped items only — full Done history not needed).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the ROADMAP update section ("อัปเดต ROADMAP") and the "Ensure all
  shipped items are in Done" instruction still work — those steps write to
  ROADMAP, not read it, so no conflict. Verify the standalone re-prioritize
  prompt for Next section still has access (it reads Next interactively at that
  point — confirm the instruction there already scopes to Next or add targeted
  read if missing).
  Run: `make test-unit` — still PASS

---

## Task 6: Update `commands/zie-release.md` — Now only

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-release.md` reads Now section targeted for scanning `[x]` items
- Does NOT instruct a bare full-file read of ROADMAP.md for the version-bump suggestion step

**Files:**
- Modify: `commands/zie-release.md`
- Modify: `tests/unit/test_roadmap_section_aware_reads.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_section_aware_reads.py — add after TestZieRetro

  class TestZieRelease:
      def test_now_section_targeted_read_present(self):
          text = read_command("zie-release.md")
          assert "Now" in text, "zie-release.md must reference Now section"

      def test_no_unqualified_full_roadmap_read(self):
          text = read_command("zie-release.md")
          assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
              "zie-release.md must not contain an unqualified full ROADMAP.md read"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-release.md`, the All Gates Passed — Release section,
  step 1 (Suggest version bump), replace:

  Before:
  ```
     - Scan `[x]` items in Now + git log since last tag
  ```

  After:
  ```
     - Grep `## Now` in `zie-framework/ROADMAP.md` → Read from that line to
       next `---` separator (Now section only) → scan `[x]` items + git log
       since last tag
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify step 3 (Update ROADMAP.md — move `[x]` items from Now to Done) is a
  write operation and unaffected by the read-scope change. The targeted Now read
  feeds the version-bump suggestion; the subsequent write targets Now and Done
  explicitly — no conflict.
  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md commands/zie-status.md commands/zie-plan.md commands/zie-spec.md commands/zie-retro.md commands/zie-release.md tests/unit/test_roadmap_section_aware_reads.py && git commit -m "feat: roadmap-section-aware-reads"`*
