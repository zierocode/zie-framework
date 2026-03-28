---
approved: true
approved_at: 2026-03-23
backlog:
spec: specs/2026-03-23-quick-spec-design.md
---

# Quick Spec — Implementation Plan

**Goal:** Extend `/zie-spec` to accept an inline idea string, skipping the
backlog file requirement.

**Architecture:** Single command file change — `commands/zie-spec.md` gains
an input-mode detection block before Step 1. When an inline idea is detected,
it passes the idea string directly to `spec-design` instead of reading a
backlog file.

**Tech Stack:** Markdown (command file), Python/pytest (content validation)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `tests/unit/test_quick_spec.py` | Validate command contains quick-spec mode |
| Modify | `commands/zie-spec.md` | Add inline idea detection + quick-spec flow |

---

## Task 1: Add quick-spec mode to `/zie-spec`

**Acceptance Criteria:**

- `commands/zie-spec.md` contains inline idea detection (spaces in arg → quick
  mode; no backlog file + single word → quick mode + warn)
- Quick mode prints "Quick spec mode — skipping backlog. Starting spec
  design..."
- Quick mode passes idea string to `spec-design` directly
- Slug derivation from idea string is documented (kebab-case first 5 words)
- ROADMAP Next update step is present for quick mode
- Existing slug flow (backlog file read) is unchanged

**Files:**

- Create: `tests/unit/test_quick_spec.py`
- Modify: `commands/zie-spec.md`

- [x] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_quick_spec.py
  from pathlib import Path

  ROOT = Path(__file__).parent.parent.parent
  COMMANDS = ROOT / "commands"


  def read_cmd(name):
      return (COMMANDS / f"zie-{name}.md").read_text()


  def test_quick_spec_mode_detection_spaces():
      content = read_cmd("spec")
      assert "spaces" in content or "contains spaces" in content


  def test_quick_spec_mode_detection_no_backlog():
      content = read_cmd("spec")
      assert "No backlog file" in content or "no backlog file" in content


  def test_quick_spec_prints_mode_message():
      content = read_cmd("spec")
      assert "Quick spec mode" in content


  def test_quick_spec_passes_idea_to_spec_design():
      content = read_cmd("spec")
      assert "spec-design" in content
      # idea string passed as context — verify inline idea path exists
      assert "inline idea" in content or "idea string" in content


  def test_quick_spec_slug_derivation():
      content = read_cmd("spec")
      assert "kebab-case" in content or "kebab" in content


  def test_quick_spec_roadmap_update():
      content = read_cmd("spec")
      assert "ROADMAP" in content


  def test_existing_slug_flow_preserved():
      content = read_cmd("spec")
      # existing backlog file read step must still be present
      assert "backlog/<slug>.md" in content or "backlog/" in content
  ```

  Run: `make test-unit` — must FAIL (quick-spec mode not in zie-spec.md yet)

- [x] **Step 2: Implement (GREEN)**

  In `commands/zie-spec.md`, replace Step 1 of the Steps section with a mode
  detection block:

  ````markdown
  ## Steps

  1. **Detect input mode:**

     - If arg is provided:
       - Check `zie-framework/backlog/<arg>.md` exists → **slug mode**: read
         backlog file → continue to step 2.
       - Arg contains spaces → **quick mode**: go to quick-spec flow below.
       - No backlog file + single word → **quick mode** + warn: "No backlog
         file found for '`<arg>`' — treating as inline idea."
     - If no arg → read ROADMAP.md Next section, list items, ask: "Which to
       spec? Enter number." → slug mode.

  2. **Slug mode** (existing flow — unchanged): pass backlog content to
     `Skill(zie-framework:spec-design)` with `zie_memory_enabled` from
     .config.

  3. **Quick spec mode** (new): print "Quick spec mode — skipping backlog.
     Starting spec design..."

     - Derive slug: kebab-case of first 5 words of idea string.
       Example: `"add rate limiting to API"` → `add-rate-limiting-to-api`
     - Check slug collision: if `zie-framework/specs/*-<slug>-design.md`
       already exists → append `-2`, `-3`, etc.
     - Pass idea string directly to `Skill(zie-framework:spec-design)` as
       context (idea becomes the problem statement — no backlog file needed).
     - spec-design asks clarifying questions, proposes approaches, writes
       spec, runs spec-reviewer loop, records `approved: true` in frontmatter.
     - After spec approved, add to ROADMAP Next:
       `- [ ] <idea title> — [spec](specs/YYYY-MM-DD-<slug>-design.md)`

  4. Print handoff (both modes):

     ```text
     Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

     Next: /zie-plan <slug> to create the implementation plan.
     ```
  ````

  Also update `argument-hint` in frontmatter:
  `"[slug|\"idea\"] — backlog slug or inline idea string"`

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Read updated `zie-spec.md` end-to-end. Verify:
  - Step numbering is consistent
  - Notes section still accurate — update if needed
  - `argument-hint` reflects both modes

  Run: `make test-unit` — still PASS

---

## Context from brain

_zie_memory_enabled=false — no brain context available._
