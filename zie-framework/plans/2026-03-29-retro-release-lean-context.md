---
approved: true
approved_at: 2026-03-29
backlog: backlog/retro-release-lean-context.md
spec: specs/2026-03-29-retro-release-lean-context-design.md
---

# Retro + Release Lean Context — Implementation Plan

**Goal:** Eliminate the ROADMAP double-read in `/zie-retro` and replace the blocking fallback in `/zie-release` with a graceful skip message plus a `make docs-sync` manual target.
**Architecture:** Two targeted edits to command Markdown files and one Makefile addition. In `zie-retro.md`, the Done section text already read in the main flow is extracted into the compact JSON bundle as `done_section_current` and forwarded to both background agents, removing any need for agents to re-read ROADMAP. In `zie-release.md`, the inline `<!-- fallback: ... Skill inline -->` comment is replaced with an explicit skip message and a note to run `make docs-sync`. The Makefile gains a `docs-sync` target that documents the manual path.
**Tech Stack:** Markdown command files (no Python changes), Makefile (GNU make), pytest structural tests

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-retro.md` | Pre-extract Done section into `done_section_current`, pass to agents, remove inline re-read instruction |
| Modify | `commands/zie-release.md` | Replace blocking fallback comment with graceful skip message |
| Modify | `Makefile` | Add `docs-sync` target |
| Create | `tests/unit/test_retro_lean_context.py` | Structural assertions for zie-retro.md changes |
| Create | `tests/unit/test_release_lean_fallback.py` | Structural assertions for zie-release.md fallback change |
| Modify | `tests/unit/test_docs_sync.py` | Assert `docs-sync` target exists in Makefile |

---

## Task 1: Structural tests for zie-retro.md lean context (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- Test asserts `done_section_current` key appears in `zie-retro.md` compact JSON bundle
- Test asserts background ADR agent prompt references `done_section_current`
- Test asserts background ROADMAP agent prompt references `done_section_current`
- Test asserts no instruction for agents to re-read ROADMAP (`"re-read"` phrase absent near agent prompts)
- All four tests FAIL before zie-retro.md is modified

**Files:**
- Create: `tests/unit/test_retro_lean_context.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_retro_lean_context.py
"""Structural tests: zie-retro.md must pre-extract Done section for agents."""
from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


class TestRetroLeanContext:
    def _src(self) -> str:
        return RETRO_MD.read_text()

    def test_compact_bundle_has_done_section_current(self):
        """Compact JSON bundle must include done_section_current field."""
        assert "done_section_current" in self._src(), (
            "zie-retro.md compact JSON bundle must include 'done_section_current' key"
        )

    def test_adr_agent_receives_done_section_current(self):
        """ADR background agent prompt must reference done_section_current."""
        src = self._src()
        # Find the ADR agent invocation block and confirm done_section_current is passed
        adr_agent_pos = src.find("Write ADRs")
        assert adr_agent_pos != -1, "ADR agent invocation not found in zie-retro.md"
        # done_section_current must appear somewhere in the ADR agent prompt region
        # (within 500 chars after the ADR agent line)
        region = src[max(0, adr_agent_pos - 100):adr_agent_pos + 500]
        assert "done_section_current" in region, (
            "ADR agent prompt must reference done_section_current to avoid re-reading ROADMAP"
        )

    def test_roadmap_agent_receives_done_section_current(self):
        """ROADMAP update background agent prompt must reference done_section_current."""
        src = self._src()
        roadmap_agent_pos = src.find("Update ROADMAP Done section")
        assert roadmap_agent_pos != -1, "ROADMAP update agent invocation not found"
        region = src[max(0, roadmap_agent_pos - 100):roadmap_agent_pos + 500]
        assert "done_section_current" in region, (
            "ROADMAP agent prompt must reference done_section_current"
        )

    def test_agents_do_not_re_read_full_roadmap(self):
        """Agent prompts must not instruct agents to re-read the full ROADMAP file."""
        src = self._src()
        # Locate the parallel agents section
        agents_section_start = src.find("### บันทึก ADRs + อัปเดต ROADMAP")
        if agents_section_start == -1:
            agents_section_start = src.find("ADRs")
        assert agents_section_start != -1, "ADRs section not found"
        # Check from agents section to end of file
        agents_region = src[agents_section_start:]
        # The agent prompts must not tell agents to re-read the full ROADMAP
        assert "re-read ROADMAP" not in agents_region, (
            "Agent prompts must not instruct re-reading ROADMAP — use done_section_current instead"
        )
        assert "read full" not in agents_region.lower(), (
            "Agent prompts must not instruct reading the full ROADMAP file"
        )
```

Run: `make test-unit` — must FAIL (4 failures: `done_section_current` not yet in zie-retro.md)

- [ ] **Step 2: Implement (GREEN)**

See Task 3 (this task only writes the tests). After Task 3 GREEN, re-run:

```bash
make test-unit
```

Expected: all 4 tests in `TestRetroLeanContext` PASS.

- [ ] **Step 3: Refactor**

No refactor needed for test file. Confirm test class name is `TestRetroLeanContext` and matches the file's module name. Run: `make test-unit` — still PASS.

---

## Task 2: Structural tests for zie-release.md fallback + Makefile docs-sync (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- Test asserts old blocking fallback comment is absent from `zie-release.md`
- Test asserts skip message `docs-sync-check unavailable` appears in `zie-release.md`
- Test asserts `make docs-sync` reference appears in `zie-release.md`
- All three tests FAIL before modifications

**Files:**
- Create: `tests/unit/test_release_lean_fallback.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_release_lean_fallback.py
"""Structural tests: zie-release.md must use graceful skip, not blocking fallback."""
from pathlib import Path

ROOT = Path(__file__).parents[2]
RELEASE_MD = ROOT / "commands" / "zie-release.md"


class TestReleaseLeanFallback:
    def _release(self) -> str:
        return RELEASE_MD.read_text()

    def test_blocking_fallback_comment_removed(self):
        """Old blocking fallback comment must be replaced — it instructs calling Skill inline."""
        src = self._release()
        # The old comment instructed calling Skill inline — this must be gone
        assert "call Skill(zie-framework:docs-sync-check) inline" not in src, (
            "Blocking fallback comment still present in zie-release.md — must be replaced"
        )

    def test_skip_message_present(self):
        """Release fallback must print a skip message, not block."""
        src = self._release()
        assert "docs-sync-check unavailable" in src, (
            "zie-release.md fallback must print 'docs-sync-check unavailable' skip message"
        )

    def test_manual_check_reference_present(self):
        """Release fallback must reference make docs-sync for manual check."""
        src = self._release()
        assert "make docs-sync" in src, (
            "zie-release.md must reference 'make docs-sync' as the manual fallback"
        )
```

Run: `make test-unit` — must FAIL (3 failures)

- [ ] **Step 2: Implement (GREEN)**

See Task 4 (this task only writes the tests). After Task 4 GREEN, re-run:

```bash
make test-unit
```

Expected: all 3 tests in `TestReleaseLeanFallback` PASS.

- [ ] **Step 3: Refactor**

No refactor needed. Run: `make test-unit` — still PASS.

---

## Task 3: Update `commands/zie-retro.md` — pre-extract Done section

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `done_section_current` key added to the compact JSON bundle definition
- The compact bundle comment explains it holds the extracted Done section text
- ADR agent prompt passes `done_section_current` from the bundle (no re-read instruction)
- ROADMAP agent prompt passes `done_section_current` from the bundle (no re-read instruction)
- ROADMAP agent uses regex replace strategy: replace `## Done\n...\n---` block with updated content
- Edge case documented: if Done section has no trailing `---`, agent uses end-of-file as boundary
- No instruction for agents to read ROADMAP independently

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing tests (RED)**

Tests already written in Task 1. Run to confirm they still fail before this edit:

```bash
make test-unit -k TestRetroLeanContext
```

Expected: 4 FAIL.

- [ ] **Step 2: Implement (GREEN)**

**Change 1 — Compact JSON bundle** (`### สร้าง compact summary` section):

Current bundle:
```json
{
  "shipped": ["<commit message 1>", "<commit message 2>"],
  "commits_since_tag": "<count from git log>",
  "pain_points": [],
  "decisions": [],
  "roadmap_done_tail": "<last 5 lines of Done section>"
}
```

Replace with:
```json
{
  "shipped": ["<commit message 1>", "<commit message 2>"],
  "commits_since_tag": "<count from git log>",
  "pain_points": [],
  "decisions": [],
  "roadmap_done_tail": "<last 5 lines of Done section>",
  "done_section_current": "<full text of Done section as read in step 3 above — passed to agents to avoid re-reading ROADMAP>"
}
```

**Change 2 — ADR agent prompt** (`### บันทึก ADRs + อัปเดต ROADMAP (parallel)` section):

Current Agent 1 prompt:
```
Agent(..., prompt="Write ADRs for decisions: {decisions_json}. Next ADR number: {next_adr_n}. Write each to zie-framework/decisions/ADR-<NNN>-<slug>.md")
```

Replace with:
```
Agent(..., prompt="Write ADRs for decisions: {decisions_json}. Next ADR number: {next_adr_n}. Write each to zie-framework/decisions/ADR-<NNN>-<slug>.md. Done section context (do not re-read ROADMAP): {done_section_current}")
```

**Change 3 — ROADMAP agent prompt** (Agent 2 in same section):

Current Agent 2 prompt:
```
Agent(..., prompt="Update ROADMAP Done section for shipped items: {shipped_items}. File: zie-framework/ROADMAP.md")
```

Replace with:
```
Agent(..., prompt="Update ROADMAP Done section for shipped items: {shipped_items}. Current Done section text: {done_section_current}. File: zie-framework/ROADMAP.md. Strategy: re-read the full file immediately before writing, then replace the Done section block (pattern: '## Done\n' to next '---' separator, or end-of-file if no trailing separator). Use a single full-file rewrite with the section replaced — no offset arithmetic needed.")
```

Run: `make test-unit -k TestRetroLeanContext` — must PASS (4 pass)

Run: `make test-unit` — full suite must still PASS

- [ ] **Step 3: Refactor**

- Confirm the `done_section_current` comment in the bundle is clear about what text it holds
- Confirm both agent prompts use `{done_section_current}` interpolation syntax consistent with other fields in the prompts
- Confirm no other agent prompt in zie-retro.md contains a bare "read ROADMAP" instruction that was missed
- Run: `make test-unit` — still PASS

---

## Task 4: Update `commands/zie-release.md` — replace blocking fallback

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- Old comment `<!-- fallback: if Agent tool unavailable, call Skill(zie-framework:docs-sync-check) inline -->` is removed
- Replacement text printed when Agent unavailable: `[zie-framework] docs-sync-check unavailable — skipping (manual check: make docs-sync)`
- Fallback instructs continuing to next gate (not blocking)
- `make docs-sync` is referenced in the fallback instruction

**Files:**
- Modify: `commands/zie-release.md`

- [ ] **Step 1: Write failing tests (RED)**

Tests already written in Task 2. Confirm they fail:

```bash
make test-unit -k TestReleaseLeanFallback
```

Expected: at minimum `test_blocking_fallback_comment_removed`, `test_skip_message_present`, `test_manual_check_reference_present` FAIL.

- [ ] **Step 2: Implement (GREEN)**

In `commands/zie-release.md`, locate the Quality Checks section. The current line reads:

```markdown
<!-- fallback: if Agent tool unavailable, call Skill(zie-framework:docs-sync-check) inline -->
```

Replace with:

```markdown
<!-- fallback: if Agent tool unavailable, print:
     `[zie-framework] docs-sync-check unavailable — skipping (manual check: make docs-sync)`
     and continue to Quality Forks without blocking. -->
```

Also update the `### รวมผลลัพธ์ Quality Forks` section. The current last bullet reads:

```markdown
- If either fork did not complete → run inline (blocking) before continuing.
```

Replace with:

```markdown
- If docs-sync-check fork did not complete (Agent unavailable) → print:
  `[zie-framework] docs-sync-check unavailable — skipping (manual check: make docs-sync)`
  and continue. Release is never blocked by a non-critical sync check.
```

Run: `make test-unit -k TestReleaseLeanFallback` — must PASS (4 pass)

Run: `make test-unit` — full suite must PASS

- [ ] **Step 3: Refactor**

- Confirm the skip message string is identical in both the fallback comment and the Quality Forks section (consistent UX)
- Confirm the existing parallel structure (docs-sync-check Agent + Bash scan in one message) is preserved
- Run: `make test-unit` — still PASS

---

## Task 5: Add `docs-sync` target to `Makefile`

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `docs-sync:` target exists in `Makefile`
- Target has a `##` comment (appears in `make help` output)
- Target body documents that `docs-sync-check` is a Claude skill (not a raw CLI command)
- Target exits gracefully (no hard error if Claude CLI absent)

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**

Add a dedicated test for the Makefile target in `tests/unit/test_release_lean_fallback.py`:

```python
class TestMakefileDocsSyncTarget:
    def _makefile(self) -> str:
        return (Path(__file__).parents[2] / "Makefile").read_text()

    def test_makefile_has_docs_sync_target(self):
        """Makefile must define a docs-sync target."""
        assert "docs-sync:" in self._makefile(), (
            "Makefile missing 'docs-sync:' target — needed as manual docs-sync-check path"
        )
```

Run to confirm it fails:

```bash
make test-unit -k test_makefile_has_docs_sync_target
```

Expected: FAIL.

- [ ] **Step 2: Implement (GREEN)**

In `Makefile`, add the `docs-sync` target after the `archive-plans` target (before `# ── Utilities`):

```makefile
docs-sync: ## Run docs-sync-check manually (checks CLAUDE.md + README.md vs disk)
	@echo "[zie-framework] docs-sync-check is a Claude skill — run inside a Claude session:"
	@echo "  Skill(zie-framework:docs-sync-check)"
	@echo "Or run /zie-retro which invokes it automatically."
```

Run: `make test-unit -k test_makefile_has_docs_sync_target` — must PASS

Run: `make test-unit` — full suite must PASS

Run: `make help` — `docs-sync` must appear in the help table

- [ ] **Step 3: Refactor**

- Confirm the `@echo` lines use consistent indentation (tab, not spaces)
- Confirm target sits between `archive-plans` and `# ── Utilities` for logical grouping
- Run: `make test-unit` — still PASS

---

## Task 6: Extend existing test coverage for retro + release structural tests

<!-- depends_on: Task 3, Task 4 -->

**Acceptance Criteria:**
- `tests/unit/test_retro_parallel.py` gains one test asserting compact bundle has `done_section_current`
- `tests/unit/test_hybrid_release.py` gains one test asserting no blocking fallback comment
- Both new tests PASS after Tasks 3 + 4 are complete
- No existing tests broken

**Files:**
- Modify: `tests/unit/test_retro_parallel.py`
- Modify: `tests/unit/test_hybrid_release.py`

- [ ] **Step 1: Write failing tests (RED)**

**Append to `tests/unit/test_retro_parallel.py`:**

```python
class TestRetroLeanContextExtension:
    def test_retro_compact_bundle_has_done_section_current(self):
        """Compact bundle must include done_section_current for lean agent context."""
        text = RETRO_MD.read_text()
        assert "done_section_current" in text, (
            "zie-retro.md compact JSON bundle must include 'done_section_current'"
        )
```

**Append to `tests/unit/test_hybrid_release.py`:**

```python
class TestReleaseLeanFallbackExtension:
    def test_zie_release_no_blocking_docs_sync_fallback(self):
        """Release must not block on docs-sync-check when Agent unavailable."""
        content = (COMMANDS / "zie-release.md").read_text()
        assert "call Skill(zie-framework:docs-sync-check) inline" not in content, (
            "Blocking inline Skill fallback must be replaced with graceful skip message"
        )
```

Run: `make test-unit` — both new tests FAIL (Tasks 3 + 4 not yet applied)

- [ ] **Step 2: Implement (GREEN)**

No implementation in this task — the tests depend on Tasks 3 and 4. After those are complete, run:

```bash
make test-unit
```

Expected: both new tests PASS.

- [ ] **Step 3: Refactor**

- Confirm no duplicate assertions across `test_retro_lean_context.py` and `test_retro_parallel.py`
- If duplication detected, remove from the older file (keep in the new dedicated file)
- Run: `make test-unit` — still PASS

---

## Task 7: Full suite verification and commit

<!-- depends_on: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6 -->

**Acceptance Criteria:**
- `make test-unit` passes with zero failures
- `make test` passes (unit + integration + md lint)
- No regression in `TestRetroSubagentSection`, `TestRetroParallel`, `TestZieRelease`, `TestZieRetro` (existing test classes)
- `commands/zie-retro.md` and `commands/zie-release.md` pass markdownlint

**Files:**
- No new files — verification only

- [ ] **Step 1: Run full test suite**

```bash
make test-unit
```

Expected: all tests pass, including new `TestRetroLeanContext`, `TestReleaseLeanFallback`, and the extended tests in `test_retro_parallel.py` + `test_hybrid_release.py`.

```bash
make test
```

Expected: unit + integration + md lint clean.

- [ ] **Step 2: Smoke-check make help**

```bash
make help
```

Expected: `docs-sync` target appears in the help table with description.

- [ ] **Step 3: Commit**

```bash
git add commands/zie-retro.md \
        commands/zie-release.md \
        Makefile \
        tests/unit/test_retro_lean_context.py \
        tests/unit/test_release_lean_fallback.py \
        tests/unit/test_retro_parallel.py \
        tests/unit/test_hybrid_release.py
git commit -m "feat: retro+release lean context — pre-extract Done section, graceful docs-sync fallback"
```

- [ ] **Step 4: Verify no regressions**

```bash
make test-unit
```

Expected: still all green.
