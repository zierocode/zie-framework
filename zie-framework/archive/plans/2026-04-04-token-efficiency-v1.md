---
approved: true
approved_at: 2026-04-04
backlog: backlog/token-efficiency-v1.md
---

# Token Efficiency v1 — Implementation Plan

**Goal:** Reduce token usage across every pipeline run by applying three targeted optimizations: ADR summary gate, CLAUDE.md cache structure, and skill/command prompt compression.
**Architecture:** (A) reviewer-context + load-context load only ADR-000-summary.md by default, fetching individual full ADRs only on topical match; (B) CLAUDE.md reordered so stable sections form a cacheable prefix; (C) all 26 skill/command files trimmed 20–30% with test-gate protection throughout.
**Tech Stack:** Markdown (skills, commands, CLAUDE.md), Python tests (pytest)

---

## File Map

| Action | File | Change |
| --- | --- | --- |
| Modify | `zie-framework/decisions/ADR-000-summary.md` | Add ADR-031 to ADR-055 as 1-line entries |
| Modify | `skills/load-context/SKILL.md` | Summary-first ADR load protocol |
| Modify | `skills/reviewer-context/SKILL.md` | Summary-first ADR load protocol |
| Modify | `skills/spec-reviewer/SKILL.md` | Inline fast-path updated for summary |
| Modify | `skills/plan-reviewer/SKILL.md` | Inline fast-path updated for summary |
| Modify | `skills/impl-reviewer/SKILL.md` | Inline fast-path updated for summary |
| Modify | `commands/retro.md` | Add auto-update ADR-000-summary.md step |
| Modify | `CLAUDE.md` | Reorder + STABLE/DYNAMIC markers |
| Modify | All 12 `skills/*/SKILL.md` | Word count audit + 20–30% compression |
| Modify | All 14 `commands/*.md` | Word count audit + 20–30% compression |

---

## Task 1: Expand ADR-000-summary.md to cover ADR-031 to ADR-055

**Acceptance Criteria:**
- `ADR-000-summary.md` contains a 1-line entry for every ADR from ADR-001 to ADR-055
- Each entry: `| ADR-NNN | Title | One-sentence decision | Status |`
- Total file ≤ 350 tokens (≤ ~600 words)

**Files:**
- Modify: `zie-framework/decisions/ADR-000-summary.md`

- [ ] **Step 1: Write failing test (RED)**
  ```python
  # tests/test_adr_summary.py
  def test_adr_summary_covers_all_adrs():
      content = Path("zie-framework/decisions/ADR-000-summary.md").read_text()
      for n in range(31, 56):
          assert f"ADR-{n:03d}" in content, f"ADR-{n:03d} missing from summary"
  ```
  Run: `make test-fast` — must FAIL

- [ ] **Step 2: Add ADR-031 to ADR-055 entries (GREEN)**
  Append to the summary table:
  ```
  | ADR-031 | ADR Session Cache | write_adr_cache/get_cached_adrs: cache ADR list per session to avoid redundant dir reads. | Accepted |
  | ADR-032 | Shared Context Bundle in zie-audit | Build context bundle once in Phase 1; pass to all parallel Phase 2 agents. | Accepted |
  | ADR-033 | Parallel Release Gates Fan-Out | Gates 2/3/4 in zie-release run in parallel; only Gate 1 must run first. | Accepted |
  | ADR-034 | Phase-Parallel Sprint Orchestration | Sprint: spec all items in parallel, implement sequentially, single batch release+retro. | Accepted |
  | ADR-035 | Pure Markdown Sprint Orchestration | /sprint implemented as Markdown command using Agent+Skill tools, not a Python hook. | Accepted |
  | ADR-036 | AST Parsing for Hooks with Module-Level Side Effects | Use AST parsing to test hooks that call sys.exit() at module level. | Accepted |
  | ADR-037 | Coverage Gate Raised to 48% | --fail-under raised from 43 to 48 after measurement fix. | Accepted |
  | ADR-038 | Hook Timing Instrumentation | Hooks emit elapsed_ms to session log for latency diagnostics. | Accepted |
  | ADR-039 | Structural Test Assertions | Replace keyword-presence tests with structural assertions (section order, field presence). | Accepted |
  | ADR-040 | Input Validation Brace Guard | Add bare brace {} to dangerous compound regex in input-sanitizer. | Accepted |
  | ADR-041 | Pre-commit Hook Simplified to Stub | Pre-commit hook is a no-op stub; enforcement moved to CI. | Accepted |
  | ADR-042 | utils.py Split into 5 Sub-modules | utils.py split into utils_event, utils_io, utils_safety, utils_roadmap, utils_backlog. | Accepted |
  | ADR-043 | Consolidate PreToolUse Hooks | input-sanitizer.py merged into safety-check.py; single PreToolUse hook. | Accepted |
  | ADR-044 | Skill Over Agent for Sequential Steps | Use Skill() invocation instead of Agent() for sequential workflow steps to avoid context overhead. | Accepted |
  | ADR-045 | ROADMAP Cache mtime-Gate | ROADMAP cache invalidated by file mtime change, not TTL expiry. | Accepted |
  | ADR-046 | Subagent Context Scoped by Agent Type | subagent-context.py emits context only for Explore and Plan agents. | Accepted |
  | ADR-047 | Retro Inline File Writes | /retro writes ADR + ROADMAP files inline; no background agents for file writes. | Accepted |
  | ADR-048 | Shared load-context Skill | load-context skill loads ADRs + context.md once per session; all reviewers reuse bundle. | Accepted |
  | ADR-049 | Drift Log NDJSON | SDLC bypass events logged as NDJSON to zie-framework/drift.log. | Accepted |
  | ADR-050 | Escape Hatch Over Hard Block | intent-sdlc.py warns and offers escape hatches instead of hard-blocking on no-track state. | Accepted |
  | ADR-051 | Command Namespace Flattening | Remove zie- prefix from all commands; invoked as /backlog, /spec, /plan, etc. | Accepted |
  | ADR-052 | Bind-Once Session-Scoped Variables | Commands read .config and ROADMAP once per execution; no repeated reads. | Accepted |
  | ADR-053 | Self-Enforcement in Framework Not Memory | Fix bad patterns by updating framework spec/skills directly, not by writing zie-memory entries. | Accepted |
  | ADR-054 | Inline Reviewer Context Hop Elimination | Reviewer skills load context inline (Phase 1 inlined) instead of invoking reviewer-context as separate hop. | Accepted |
  | ADR-055 | Sprint Phase 2 Collapse | Sprint Phase 2 (plan) folded into Phase 1 parallel; spec+plan run as single concurrent wave. | Accepted |
  ```
  Run: `make test-fast` — must PASS

- [ ] **Step 3: Refactor**
  Verify `wc -w zie-framework/decisions/ADR-000-summary.md` ≤ 600 words.

---

## Task 2: Update load-context + reviewer-context for summary-first protocol

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `load-context` Step 1 reads `ADR-000-summary.md` first; Step 2 conditionally loads specific full ADRs on topical relevance
- `reviewer-context` same protocol in disk fallback path
- Fallback to full ADR load when `ADR-000-summary.md` missing, emitting stderr warning
- `context_bundle` pass-through fast-path unchanged

**Files:**
- Modify: `skills/load-context/SKILL.md`
- Modify: `skills/reviewer-context/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_skills_load_context.py
  def test_load_context_reads_summary_first():
      content = Path("skills/load-context/SKILL.md").read_text()
      assert "ADR-000-summary.md" in content
      # summary load must precede full ADR fallback mention
      assert content.index("ADR-000-summary.md") < content.index("decisions/ADR-")

  def test_load_context_fallback_on_missing_summary():
      content = Path("skills/load-context/SKILL.md").read_text()
      assert "missing" in content.lower() or "absent" in content.lower()
      assert "fall back" in content.lower() or "fallback" in content.lower()

  # tests/test_skills_reviewer_context.py
  def test_reviewer_context_reads_summary_first():
      content = Path("skills/reviewer-context/SKILL.md").read_text()
      assert "ADR-000-summary.md" in content
      assert content.index("ADR-000-summary.md") < content.index("decisions/ADR-")
  ```
  Run: `make test-fast` — must FAIL

- [ ] **Step 2: Update both skills (GREEN)**

  Replace `load-context` ADR loading steps:
  ```markdown
  **Step 0: Cache check**
  - Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
    - Cache hit → `adrs_content` ← returned value; skip Steps 1–2.
    - Cache miss → proceed to Step 1.

  **Step 1: Load ADR summary**
  - Read `zie-framework/decisions/ADR-000-summary.md` → `adrs_content`.
  - If file missing → fall back: read all `decisions/ADR-*.md` (current behavior);
    emit `[zie-framework] ADR summary missing — using full load` to stderr.

  **Step 2: Summary returned as adrs_content**
  - `adrs_content` ← summary file content. No topic matching in load-context.
  - Reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) are responsible
    for reading the summary and deciding whether to load a specific full ADR from
    disk based on what they're reviewing. load-context just loads and returns the
    summary.
  ```

  Apply equivalent update to `reviewer-context` disk fallback section.
  Run: `make test-fast` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `wc -w` reduction vs baseline (load-context was 213, reviewer-context was 202).

---

## Task 3: Update inline fast-paths in spec/plan/impl-reviewer

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `spec-reviewer`, `plan-reviewer`, `impl-reviewer` Phase 1 disk fallback reads `ADR-000-summary.md` first
- Full ADR files loaded only when topically relevant
- Fast-path (`context_bundle` provided) unchanged

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_skills_reviewers.py
  import pytest
  from pathlib import Path

  @pytest.mark.parametrize("skill", ["spec-reviewer", "plan-reviewer", "impl-reviewer"])
  def test_reviewer_inline_fastpath_uses_summary(skill):
      content = Path(f"skills/{skill}/SKILL.md").read_text()
      assert "ADR-000-summary.md" in content
  ```
  Run: `make test-fast` — must FAIL

- [ ] **Step 2: Update reviewer Phase 1 disk fallback (GREEN)**
  In each reviewer's Phase 1 inline fast-path, replace:
  ```
  cache miss → read `decisions/*.md` (including `ADR-000-summary.md`)
  ```
  with:
  ```
  cache miss → read `decisions/ADR-000-summary.md` → `adrs_content`;
  if missing → read all `decisions/ADR-*.md` (fallback);
  if topically relevant full ADRs needed → load specific files from disk.
  ```
  Run: `make test-fast` — must PASS

- [ ] **Step 3: Refactor**
  Verify the three files have consistent Phase 1 language.

---

## Task 4: Update retro.md for auto-update of ADR-000-summary.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/retro.md` includes a step to append new ADRs to `ADR-000-summary.md` after retro writes new ADR files
- Step uses haiku model for the summary update
- Step is skipped if no new ADRs were written this session

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing test (RED)**
  ```python
  # tests/test_commands_retro.py (add to existing)
  def test_retro_updates_adr_summary():
      content = Path("commands/retro.md").read_text()
      assert "ADR-000-summary.md" in content
      # must appear in the step that runs after ADR file writes
      assert "summary" in content.lower()
  ```
  Run: `make test-fast` — must FAIL

- [ ] **Step 2: Add summary-update step to retro.md (GREEN)**
  After the ADR file-write step in retro.md, insert:
  ```markdown
  **ADR-000-summary.md update** — if new ADR files were written this session:
  - Spawn haiku agent: read each new ADR file → append 1-line entry to
    `zie-framework/decisions/ADR-000-summary.md` in table format:
    `| ADR-NNN | Title | One-sentence decision | Status |`
  - Skip if no new ADRs written.
  ```
  Run: `make test-fast` — must PASS

- [ ] **Step 3: Refactor**
  Confirm step placement is correct (after ADR writes, before commit).

---

## Task 5: Reorder CLAUDE.md with STABLE/DYNAMIC markers

**Acceptance Criteria:**
- `<!-- STABLE: do not move below dynamic section -->` appears before Project Structure section
- `<!-- DYNAMIC: version-specific, ok to change -->` appears before Tech Stack section
- STABLE marker appears before DYNAMIC marker in the file
- `make test-unit` passes

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing test (RED)**
  ```python
  # tests/test_claudemd.py (add to existing or create)
  def test_claudemd_stable_dynamic_markers():
      content = Path("CLAUDE.md").read_text()
      assert "<!-- STABLE" in content
      assert "<!-- DYNAMIC" in content
      assert content.index("<!-- STABLE") < content.index("<!-- DYNAMIC")

  def test_claudemd_tech_stack_in_dynamic_section():
      content = Path("CLAUDE.md").read_text()
      dynamic_pos = content.index("<!-- DYNAMIC")
      tech_stack_pos = content.index("## Tech Stack")
      assert tech_stack_pos > dynamic_pos
  ```
  Run: `make test-fast` — must FAIL

- [ ] **Step 2: Reorder CLAUDE.md (GREEN)**
  New section order:
  1. `<!-- STABLE: do not move below dynamic section -->`
  2. `## Project Structure`
  3. `## Key Rules`
  4. `## Hook Reference Docs`
  5. `## SDLC Commands` (table)
  6. `## Development Commands`
  7. `<!-- DYNAMIC: version-specific, ok to change -->`
  8. `## Tech Stack` (contains version refs)
  9. Any optional dependency notes

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read through reordered CLAUDE.md — confirm flow is still coherent.

---

## Task 6: Compress skill files (12 files)

<!-- depends_on: Task 3 -->
<!-- Note: T3 depends_on T2, which modifies load-context/SKILL.md and reviewer-context/SKILL.md.
     T6 compresses ALL 12 skills including those two files — T6 runs after T3 is complete,
     so T2's changes are already in place before T6 touches those files. -->

**Acceptance Criteria:**
- Each of the 12 skill files has ≥ 15% word count reduction from baseline
- `make test-unit` passes after all changes
- No checklist items, required steps, output format specs, or test-enforced lines removed

**Files:**
- Modify: all `skills/*/SKILL.md` (12 files)

Baseline word counts:
```
zie-audit/SKILL.md       819
spec-design/SKILL.md     776
plan-reviewer/SKILL.md   755
write-plan/SKILL.md      583
impl-reviewer/SKILL.md   564
verify/SKILL.md          556
spec-reviewer/SKILL.md   500
docs-sync-check/SKILL.md 380
tdd-loop/SKILL.md        374
test-pyramid/SKILL.md    347
debug/SKILL.md           322
load-context/SKILL.md    213
reviewer-context/SKILL.md 202
```

- [ ] **Step 1: Grep test suite for each file (RED — safety check)**
  ```bash
  for skill in skills/*/SKILL.md; do
    name=$(basename $(dirname $skill))
    echo "=== $name ===" && grep -r "$name" tests/ | wc -l
  done
  ```
  Note which lines in each skill are tested — do not remove those.

- [ ] **Step 2: Trim each skill file (GREEN)**
  Per file, remove:
  - Phase header prose that restates what the step list already says
  - "Notes" sections that restate rules already in the checklist
  - Fallback instructions that repeat default behavior without adding info
  - Verbose output format examples where a 1-line inline example suffices

  After each file: `make test-fast` — must PASS before moving to next.

- [ ] **Step 3: Measure + verify (REFACTOR)**
  ```bash
  wc -w skills/*/SKILL.md | sort -rn
  ```
  Confirm each file is ≤ 85% of its baseline word count.
  Run: `make test-unit` — full suite must PASS.

---

## Task 7: Compress command files (14 files)

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- Each of the 14 command files has ≥ 15% word count reduction from baseline
- `make test-unit` passes after all changes
- No checklist items, required steps, or test-enforced lines removed

**Files:**
- Modify: all `commands/*.md` (14 files)

Baseline word counts:
```
init.md     1884
sprint.md   1191
retro.md    1135
plan.md      950
release.md   928
status.md    819
implement.md 736
spec.md      627
resync.md    491
fix.md       436
backlog.md   399
hotfix.md    276
spike.md     252
chore.md     217
audit.md      73
```

- [ ] **Step 1: Grep test suite for each file (RED — safety check)**
  ```bash
  for cmd in commands/*.md; do
    name=$(basename $cmd .md)
    echo "=== $name ===" && grep -r "$name" tests/ | wc -l
  done
  ```

- [ ] **Step 2: Trim each command file (GREEN)**
  Same rules as Task 6. Highest ROI: `init.md` (1884w), `sprint.md` (1191w), `retro.md` (1135w).
  After each file: `make test-fast` — must PASS before moving to next.
  Note: `audit.md` (73w) — skip, already minimal.

- [ ] **Step 3: Measure + verify (REFACTOR)**
  ```bash
  wc -w commands/*.md | sort -rn
  ```
  Confirm total word count reduction ≥ 15% across all 14 files.
  Run: `make test-unit` — full suite must PASS.

---

## Execution Order

```
T1 (ADR-000 expand)  ──┬── T2 (load/reviewer-context) ── T3 (reviewer fast-paths) ── T6 (skill compress)
                        └── T4 (retro auto-update) ──────────────────────────────── T7 (cmd compress)
T5 (CLAUDE.md)  (independent)
```

T6 and T7 can run in parallel (no file overlap).
T5 can start any time independently.
