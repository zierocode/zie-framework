---
approved: false
approved_at:
backlog: backlog/retro-inline-format.md
---

# Retro Inline Format — Implementation Plan

**Goal:** Eliminate two text-processing background agents (`retro-format`, `docs-sync-check`) in `/zie-retro` by replacing them with inline reasoning steps and Bash/Glob/Read operations. Preserve the two file-writing agents (ADR writer, ROADMAP updater) unchanged.
**Architecture:** Pure markdown edit to `commands/zie-retro.md` — no Python, no hooks, no test files. Removes two `Agent(run_in_background=True)` calls for text-processing, adds inline retro-format reasoning block, adds inline Glob+Read+compare docs-sync block. File-writing agents for ADRs and ROADMAP remain. Skills deprecated with notices.
**Tech Stack:** Markdown, Bash (inline conditional skip logic), Glob/Read for docs-sync check, Python one-liner (optional, fallback to Bash for skip guard).

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-retro.md` | Remove 2 background agent calls; add inline retro-format reasoning; add inline docs-sync Glob+Read+compare; remove fallback comment |
| Modify | `skills/retro-format/SKILL.md` | Add deprecation notice to frontmatter and body |
| Modify | `skills/docs-sync-check/SKILL.md` | Add deprecation notice to frontmatter and body |

---

## Task Sizing

5 tasks (M plan). T1 is observation-only. T2–T3 each replace one agent + remove prose. T4–T5 add deprecation notices to two skill files (independent, can parallelize if careful to avoid merge conflicts). T6 is verification.

---

## Task 1: Locate and map the two text-processing Agent() calls in zie-retro.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- Both Agent() calls are located and documented (line ranges, section names).
- Confirms the structure: retro-format Agent (lines ~60–67) and docs-sync-check Agent (lines ~66–68, same block), both with `run_in_background=True`.
- Notes the fallback comment location (lines ~73, will be removed per spec AC9).

**Files:**
- Read: `commands/zie-retro.md`

- [ ] **Step 1: Observe (RED — locate)**
  Read `commands/zie-retro.md` in full. Identify:
  1. First Agent() call for retro-format (around lines ~60–67) — `"Format retrospective summary. You are a retro format assistant..."`
  2. Second Agent() call for docs-sync-check (around lines ~66–68) — `"Check docs sync for changed files..."`
  Both within "Invoke Background Agents" section.
  Note: Both are in the same TaskCreate/Agent block (concurrent). A single fallback comment follows both (line ~73).
  Run: (no test — observation task)

- [ ] **Step 2: Document (GREEN)**
  Confirm both Agent() calls are in scope. Note that the fallback comment `<!-- fallback: if Agent unavailable, call Skill(...) inline -->` applies to both agents and must be removed entirely (AC9).

- [ ] **Step 3: No refactor needed**
  Proceed to T2.

---

## Task 2: Inline retro-format — replace Agent() with reasoning step; remove from TaskCreate

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- "Invoke Background Agents" section contains zero `Agent(` calls for retro-format.
- Retro formatting is described as a prose reasoning step (no Agent spawn).
- Output structure (five sections: สิ่งที่ Ship, สิ่งที่ทำงานได้ดี, สิ่งที่เจ็บปวด, การตัดสินใจสำคัญ, Pattern ที่ควรจำ) is identical to current skill output.
- Docs-sync Agent() still present (removed in T3).

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing test (RED)**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "format retrospective\|retro format\|Format retro"
  ```
  Must show match (old Agent() still present before edit).

- [ ] **Step 2: Implement (GREEN)**
  Replace the retro-format Agent() within the "Invoke Background Agents" block:

  **Remove** (lines ~60–67):
  ```
  1. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Format retrospective summary. You are a retro format assistant. Given compact_json: {compact_json}. Structure output as five sections: (1) สิ่งที่ Ship ออกไป — list shipped features/fixes; (2) สิ่งที่ทำงานได้ดี — what worked well; (3) สิ่งที่เจ็บปวด — pain points; (4) การตัดสินใจสำคัญ — key decisions with lasting consequences; (5) Pattern ที่ควรจำ — reusable techniques. ADR format: Status, Context, Decision, Consequences. Return full five-section retro text.")`
  ```

  **Replace with:**
  ```
  1. **Format retrospective inline.** Using `compact_json` from the context above, structure output as five sections:
     - **สิ่งที่ Ship ออกไป** — list shipped features/fixes with versions
     - **สิ่งที่ทำงานได้ดี** — patterns, approaches, tools that saved time (only worth repeating)
     - **สิ่งที่เจ็บปวด** — friction points, unexpected complexity, slowdowns (specific, not vague)
     - **การตัดสินใจสำคัญ** — decisions with lasting consequences; each: what → why → consequence (candidates for ADRs)
     - **Pattern ที่ควรจำ** — reusable techniques worth storing in brain as P1/P2 memories

     Print the five sections immediately after formatting. Candidates for ADRs (decisions with lasting consequences) are passed to the ADR writer agent below.
  ```

  Also keep the TaskCreate line for retro-format (not removed, just no Agent() call following it; context remains).

- [ ] **Step 3: Verify**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "format retrospective\|retro format"
  ```
  Must return zero matches.
  ```bash
  grep -n "สิ่งที่ Ship ออกไป" commands/zie-retro.md
  ```
  Must show at least one match (the inline section heading is now in prose, not in Agent prompt).

---

## Task 3: Inline docs-sync-check — replace Agent() with Glob+Read+compare block; remove fallback comment

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- "Invoke Background Agents" section contains zero `Agent(` calls for docs-sync-check.
- Docs-sync check is performed inline via Glob (commands/*.md, skills/*/SKILL.md, hooks/*.py) → Read CLAUDE.md → Read README.md → compare.
- Conditional skip guard for `release:` prefix is preserved exactly (if last commit starts with `release:`, skip docs-sync; print skip message).
- Fallback comment `<!-- fallback: ... -->` is removed entirely.
- Result handling ("Docs-sync skip guard", "In sync" / "Updated CLAUDE.md: ..." / "Updated README.md: ...") is inlined.

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing test (RED)**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "docs sync\|Check docs sync"
  ```
  Must show match (old Agent() still present before edit).

- [ ] **Step 2: Implement (GREEN)**
  Replace the docs-sync-check Agent() and remove the fallback comment:

  **Remove Agent()** (lines ~66–68):
  ```
  2. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Check docs sync for changed files: {changed_files}. Scan zie-framework/commands/*.md (extract /zie-* command names), zie-framework/skills/*/*.md (extract skill names), zie-framework/hooks/*.py (extract hook events). Check CLAUDE.md Development Commands section lists all commands. Check README.md skills table lists all skills. Return JSON: { 'in_sync': bool, 'missing_from_docs': [...], 'extra_in_docs': [...], 'details': str }")`
  ```

  **Remove fallback comment** (line ~73):
  ```
  <!-- fallback: if Agent unavailable, call Skill(zie-framework:retro-format) and Skill(zie-framework:docs-sync-check) inline -->
  ```
  Delete this line entirely.

  **Replace Agent() with inline block:**
  ```
  2. **Check docs sync inline.** 
     Skip guard: if `git log -1 --format="%s"` starts with `release:` → print `"Docs-sync: skipped (ran during release)"` and skip the rest of this block.
     
     Otherwise, run inline:
     1. Glob `zie-framework/commands/*.md` → extract base names (strip `.md`) → command names
     2. Glob `zie-framework/skills/*/SKILL.md` → extract parent directory names → skill names
     3. Glob `zie-framework/hooks/*.py` → extract base names (exclude `utils.py`) → hook file names
     4. Read `CLAUDE.md` — check Development Commands section and skills table for all command/skill names
     5. Read `README.md` — check commands/skills tables for all command/skill names
     6. Compare: 
        - `missing_from_docs` = on disk but not in docs
        - `extra_in_docs` = in docs but not on disk
     7. Print verdict:
        - If in sync: `"CLAUDE.md in sync | README.md in sync"`
        - If stale: update `CLAUDE.md` and/or `README.md` inline (Read/Edit/Write each), print `"Updated CLAUDE.md: added <X>, removed <Y>"` / `"Updated README.md: added <X>, removed <Y>"`
  ```

  No TaskCreate call needed for this inline block (no background execution).

- [ ] **Step 3: Verify**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "docs sync"
  ```
  Must return zero matches.
  ```bash
  grep -n "fallback" commands/zie-retro.md
  ```
  Must return zero matches (fallback comment gone).
  ```bash
  grep -n "Skip guard\|release:" commands/zie-retro.md
  ```
  Must show at least one match for the skip guard (still present in inline block).

---

## Task 4: Add deprecation notice to skills/retro-format/SKILL.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- Frontmatter contains `deprecated: true`, `deprecated_since: "2026-04-04"`, `deprecated_reason: "..."`
- Body has deprecation notice at top (below frontmatter): `> **DEPRECATED** (2026-04-04): ...`
- File is not deleted; kept for reference/fallback documentation.

**Files:**
- Modify: `skills/retro-format/SKILL.md`

- [ ] **Step 1: Read and edit (RED)**
  Read current frontmatter (lines 1–9).

- [ ] **Step 2: Add deprecation to frontmatter (GREEN)**
  Insert three new lines in frontmatter after `context: fork`:
  ```yaml
  deprecated: true
  deprecated_since: "2026-04-04"
  deprecated_reason: "Logic inlined into /zie-retro command. Skill no longer called."
  ```
  Exact insertion point: after line 8 (`context: fork`), before the `---` closing delimiter.

- [ ] **Step 3: Add deprecation notice to body**
  Insert after closing `---` (after line 9), before the first heading:
  ```markdown
  > **DEPRECATED** (2026-04-04): This skill is no longer invoked by /zie-retro.
  > The retro-format logic is now inlined directly in the command.
  > Kept for reference only. Do not invoke.

  ```
  (Include blank line after notice, before next section.)

- [ ] **Step 4: Verify**
  ```bash
  grep -n "deprecated: true" skills/retro-format/SKILL.md
  ```
  Must show match.
  ```bash
  grep -n "DEPRECATED" skills/retro-format/SKILL.md
  ```
  Must show match.

---

## Task 5: Add deprecation notice to skills/docs-sync-check/SKILL.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- Frontmatter contains `deprecated: true`, `deprecated_since: "2026-04-04"`, `deprecated_reason: "..."`
- Body has deprecation notice at top (below frontmatter): `> **DEPRECATED** (2026-04-04): ...`
- File is not deleted; kept for reference/fallback documentation.

**Files:**
- Modify: `skills/docs-sync-check/SKILL.md`

- [ ] **Step 1: Read and edit (RED)**
  Read current frontmatter (lines 1–10).

- [ ] **Step 2: Add deprecation to frontmatter (GREEN)**
  Insert three new lines in frontmatter after the last key (`effort: low`), before the closing `---` delimiter:
  ```yaml
  deprecated: true
  deprecated_since: "2026-04-04"
  deprecated_reason: "Logic inlined into /zie-retro and /zie-release commands. Skill no longer called."
  ```
  Exact insertion point: after line 9 (`effort: low`), before the `---` closing delimiter.

- [ ] **Step 3: Add deprecation notice to body**
  Insert after closing `---` (after line 10), before the first heading:
  ```markdown
  > **DEPRECATED** (2026-04-04): This skill is no longer invoked by /zie-retro or /zie-release.
  > The docs-sync-check logic is now inlined directly in these commands.
  > Kept for reference only. Do not invoke.

  ```
  (Include blank line after notice, before next section.)

- [ ] **Step 4: Verify**
  ```bash
  grep -n "deprecated: true" skills/docs-sync-check/SKILL.md
  ```
  Must show match.
  ```bash
  grep -n "DEPRECATED" skills/docs-sync-check/SKILL.md
  ```
  Must show match.

---

## Task 6: Verification grep pass — confirm AC compliance

<!-- depends_on: Task 3, Task 4, Task 5 -->

**Acceptance Criteria:**
- Zero `Agent(` calls for text-processing (retro-format, docs-sync-check) in `commands/zie-retro.md`.
- Zero fallback comments in `commands/zie-retro.md`.
- Inline retro-format block with five section headings present.
- Inline docs-sync block with skip guard (`release:`) present.
- Agent() calls for ADRs and ROADMAP updater still present (file-writing, justified).
- Both skills have deprecation notices (frontmatter + body).

**Files:**
- Read: `commands/zie-retro.md`, `skills/retro-format/SKILL.md`, `skills/docs-sync-check/SKILL.md`

- [ ] **Step 1: Grep — no text-processing Agent() calls (AC-1)**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "format retrospective\|Check docs sync\|retro-format\|docs-sync-check"
  ```
  Expected: zero output.

- [ ] **Step 2: Grep — file-writing Agent() calls still present (AC-3, AC-6)**
  ```bash
  grep -n "Agent(" commands/zie-retro.md | grep -i "ADR\|ROADMAP\|Write ADRs\|Update ROADMAP"
  ```
  Expected: ≥2 matches (ADR writer, ROADMAP updater).

- [ ] **Step 3: Grep — no fallback comments (AC-9)**
  ```bash
  grep -n "fallback" commands/zie-retro.md
  ```
  Expected: zero output.

- [ ] **Step 4: Grep — inline retro-format block present (AC-2)**
  ```bash
  grep -n "สิ่งที่ Ship ออกไป\|สิ่งที่ทำงานได้ดี\|สิ่งที่เจ็บปวด\|การตัดสินใจสำคัญ\|Pattern ที่ควรจำ" commands/zie-retro.md
  ```
  Expected: ≥5 matches (all five section headings present in inline block, not in Agent prompt).

- [ ] **Step 5: Grep — inline docs-sync block + skip guard present (AC-4)**
  ```bash
  grep -n "Skip guard\|release:" commands/zie-retro.md
  ```
  Expected: ≥1 match for skip guard.
  ```bash
  grep -n "Glob.*commands\|Glob.*skills\|Glob.*hooks" commands/zie-retro.md
  ```
  Expected: ≥3 matches for the three Glob operations.

- [ ] **Step 6: Grep — retro-format skill deprecated (AC-7)**
  ```bash
  grep -n "deprecated: true" skills/retro-format/SKILL.md
  ```
  Expected: ≥1 match.
  ```bash
  grep -n "DEPRECATED" skills/retro-format/SKILL.md
  ```
  Expected: ≥1 match.

- [ ] **Step 7: Grep — docs-sync-check skill deprecated (AC-8)**
  ```bash
  grep -n "deprecated: true" skills/docs-sync-check/SKILL.md
  ```
  Expected: ≥1 match.
  ```bash
  grep -n "DEPRECATED" skills/docs-sync-check/SKILL.md
  ```
  Expected: ≥1 match.

- [ ] **Step 8: Read command file sanity check**
  Read `commands/zie-retro.md` sections: "สร้าง compact summary" (should be unchanged), "Invoke Background Agents" (should have zero text-processing Agent() calls but still have TaskCreate lines), "รวมผลลัพธ์ forks" (should mention inline retro-format output and inline docs-sync verdict), "บันทึก ADRs + อัปเดต ROADMAP" (should still have Agent() calls for file writing).
  Confirm all sections make sense and no prose is orphaned.

---

## Completion Checklist

- [ ] T1: Both Agent() calls located (retro-format and docs-sync-check)
- [ ] T2: retro-format → inline reasoning block (5 Thai sections) ✓
- [ ] T3: docs-sync-check → inline Glob+Read+compare, skip guard preserved, fallback removed ✓
- [ ] T4: retro-format skill marked deprecated (frontmatter + body) ✓
- [ ] T5: docs-sync-check skill marked deprecated (frontmatter + body) ✓
- [ ] T6: Verification grep pass — 0 text-processing Agent() calls, ≥2 file-writing Agent() calls, all deprecation notices present ✓
