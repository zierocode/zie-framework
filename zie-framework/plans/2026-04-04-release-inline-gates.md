---
approved: false
approved_at:
backlog: backlog/release-inline-gates.md
---

# Release Inline Gates — Implementation Plan

**Goal:** Replace all 4 `Agent()` gate spawns in `commands/zie-release.md` with parallel `Bash` tool calls using `run_in_background=True`, eliminating subagent overhead while preserving identical gate semantics.
**Architecture:** Pure markdown edit — no Python, no hooks, no test files. All changes are prose/pseudocode rewrites inside `commands/zie-release.md`. The gate ordering (Pre-Gate-1 → Gate 1 → Gates 2–4 → Gate 5) stays fixed; only the execution mechanism changes from Agent() to Bash tool calls.
**Tech Stack:** Markdown, Bash (inline tool calls), Python one-liner for docs-sync check.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-release.md` | Replace 4 Agent() gate blocks with inline Bash tool calls |

---

## Task Sizing

5 tasks (M plan). T1–T4 each touch distinct sections of the same file so they must serialize. T5 is verification (read-only).

---

## Task 1: Read current command and identify all Agent() gate blocks

<!-- depends_on: none -->

**Acceptance Criteria:**
- All 4 Agent() call sites are located and documented (line numbers, section names).
- Confirms the gate structure: Pre-Gate-1 (docs-sync), Gate 2 (integration), Gate 3 (e2e), Gate 4 (visual).

**Files:**
- Read: `commands/zie-release.md`

- [ ] **Step 1: Read (RED — locate)**
  Read `commands/zie-release.md` in full. Identify:
  1. Pre-Gate-1 Agent() block (docs-sync-check) — lines ~29–36
  2. Gate 2 Agent() call — inside "Parallel Gates 2–4" section, lines ~54–58
  3. Gate 3 Agent() call — same block
  4. Gate 4 Agent() call — same block
  Note each section heading, the full Agent() call, and the fallback comment below each.
  Run: (no test — observation task)

- [ ] **Step 2: Document (GREEN)**
  Confirm all 4 Agent() calls are in scope. Note the fallback `<!-- fallback: ... -->` comment after each group — these will be removed per spec AC9.

- [ ] **Step 3: No refactor needed**
  Proceed to T2.

---

## Task 2: Rewrite Pre-Gate-1 (docs-sync) from Agent() to inline Bash

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Pre-Gate-1 section contains zero `Agent(` calls.
- Uses a Bash tool call (with `run_in_background=True` annotation) running a `python3 -c` one-liner.
- Fallback comment is removed.
- Result collection prose updated to reflect inline Bash output (not Agent result).

**Files:**
- Modify: `commands/zie-release.md`

- [ ] **Step 1: Write failing test (RED)**
  ```bash
  grep -n "Agent(" commands/zie-release.md | grep -i "docs-sync\|Check docs sync\|Check CLAUDE"
  ```
  Must show matches (confirming the old Agent() call exists before the edit).

- [ ] **Step 2: Implement (GREEN)**
  Replace the Pre-Gate-1 section block:

  **Remove** (lines ~29–36):
  ```
  Spawn docs-sync-check before unit tests — runs concurrently:

  ```python
  TaskCreate(subject="Check docs sync", description="Check CLAUDE.md/README.md against changed files", activeForm="Checking docs sync")
  Agent(subagent_type="general-purpose", run_in_background=True, prompt="Check CLAUDE.md and README.md for staleness. (1) Scan zie-framework/commands/*.md — extract all /zie-* command names. (2) Scan zie-framework/skills/*/*.md — extract all skill names. (3) Scan zie-framework/hooks/*.py — extract hook event types. (4) Check CLAUDE.md Development Commands section lists all commands. (5) Check README.md skills table lists all skills. Report: [docs-sync] PASSED or [docs-sync] FAILED: <what's stale>. Return JSON: { 'in_sync': bool, 'missing_from_docs': [...], 'extra_in_docs': [...], 'details': str }")
  ` ` `

  <!-- fallback: if Agent unavailable → print `[zie-framework] docs-sync-check unavailable — skipping` and continue. Manual check: make docs-sync -->
  ```

  **Replace with:**
  ```
  Run docs-sync check before unit tests — concurrently (run_in_background=True):

  ```bash
  # run_in_background=True
  python3 -c "
  import re, pathlib, sys
  cmds_dir = pathlib.Path('commands')
  skills_dir = pathlib.Path('skills')
  claude_md = pathlib.Path('CLAUDE.md').read_text()
  readme = pathlib.Path('README.md').read_text()
  commands = [f.stem for f in cmds_dir.glob('zie-*.md')]
  skills = [f.parent.name for f in skills_dir.glob('*/SKILL.md')]
  missing = [c for c in commands if c not in claude_md]
  missing += [s for s in skills if s not in readme]
  if missing:
      print('[docs-sync] FAILED:', missing)
      sys.exit(1)
  print('[docs-sync] PASSED')
  "
  ` ` `

  Collect result with other gate results (see "Collect Parallel Gate Results" below).
  On `[docs-sync] FAILED` → update stale docs inline (Read/Edit/Write) before version bump.
  ```

  Also update "Collect Parallel Gate Results" prose: change "docs-sync-check result (Pre-Gate-1 Agent)" → "docs-sync-check result (Pre-Gate-1 Bash)".

- [ ] **Step 3: Verify**
  ```bash
  grep -n "Agent(" commands/zie-release.md | grep -i "docs-sync\|Check CLAUDE"
  ```
  Must return zero matches.
  ```bash
  grep -n "run_in_background=True" commands/zie-release.md
  ```
  Must show at least one match for the docs-sync Bash block.

---

## Task 3: Rewrite Gate 2 (integration tests) from Agent() to inline Bash

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- Gate 2 section contains zero `Agent(` calls.
- Uses a Bash tool call with `run_in_background=True` annotation running `make test-int`.
- Reports `[Gate 2/5] PASSED`, `[Gate 2/5] SKIPPED`, or `[Gate 2/5] FAILED: <stderr>`.

**Files:**
- Modify: `commands/zie-release.md`

- [ ] **Step 1: Write failing test (RED)**
  ```bash
  grep -n "Agent(" commands/zie-release.md | grep -i "integration\|test-int\|Gate 2"
  ```
  Must show match (old Agent() still present before edit).

- [ ] **Step 2: Implement (GREEN)**
  Replace the Gate 2 Agent() call within the "Parallel Gates 2–4" block:

  **Remove:**
  ```
  Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run integration tests: execute `make test-int`. Report result: [Gate 2/5] PASSED or [Gate 2/5] FAILED: <reason>. If no integration tests exist, report [Gate 2/5] SKIPPED.")
  ```

  **Replace with:**
  ```
  ```bash
  # [Gate 2/5] Integration tests — run_in_background=True
  make test-int
  ` ` `
  Report: `[Gate 2/5] PASSED`, `[Gate 2/5] SKIPPED` (if no integration tests), or `[Gate 2/5] FAILED: <stderr>`.
  ```

- [ ] **Step 3: Verify**
  ```bash
  grep -n "Agent(" commands/zie-release.md | grep -i "integration\|test-int"
  ```
  Must return zero matches.

---

## Task 4: Rewrite Gate 3 (e2e) and Gate 4 (visual) from Agent() to conditional inline Bash; remove fallback comments

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- Gate 3 Agent() call is replaced with a conditional inline Bash block (skip if `playwright_enabled=false`, read from `.config` inline before issuing the Bash call).
- Gate 4 Agent() call is replaced with a conditional inline Bash block (skip if `has_frontend=false` OR `playwright_enabled=false`, check inline).
- Both fallback `<!-- fallback: ... -->` comments are removed.
- No `Agent(` calls remain in the entire Parallel Gates 2–4 section.
- The Bash call for Gate 3 and Gate 4 is never issued when the skip condition is true.

**Files:**
- Modify: `commands/zie-release.md`

- [ ] **Step 1: Write failing test (RED)**
  ```bash
  grep -n "Agent(" commands/zie-release.md | grep -i "e2e\|visual\|playwright\|has_frontend\|Gate 3\|Gate 4"
  ```
  Must show matches for Gate 3 and Gate 4 Agent() calls.

- [ ] **Step 2: Implement (GREEN)**
  Replace the Gate 3 and Gate 4 Agent() calls and the trailing fallback comment:

  **Remove Gate 3 Agent():**
  ```
  Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run e2e tests if enabled: check playwright_enabled in zie-framework/.config. If true, execute `make test-e2e`. If false, skip. Report: [Gate 3] PASSED or [Gate 3] SKIPPED or [Gate 3] FAILED: <reason>.")
  ```

  **Replace with:**
  ```
  **Gate 3 — E2E tests (conditional):**
  Read `playwright_enabled` from `zie-framework/.config` inline.
  - If `playwright_enabled=false` → print `[Gate 3/5] SKIPPED` (no Bash call issued).
  - If `playwright_enabled=true`:
    ```bash
    # [Gate 3/5] E2E tests — run_in_background=True
    make test-e2e
    ` ` `
    Report: `[Gate 3/5] PASSED` or `[Gate 3/5] FAILED: <stderr>`.
  ```

  **Remove Gate 4 Agent():**
  ```
  Agent(subagent_type="general-purpose", run_in_background=True, prompt="Visual check if applicable: check has_frontend and playwright_enabled in zie-framework/.config. If has_frontend=true and playwright_enabled=false, start dev server and verify key pages load without console errors. Report: [Gate 4] PASSED or [Gate 4] SKIPPED or [Gate 4] FAILED: <reason>.")
  ```

  **Replace with:**
  ```
  **Gate 4 — Visual check (conditional):**
  Read `has_frontend` and `playwright_enabled` from `zie-framework/.config` inline.
  - If `has_frontend=false` OR `playwright_enabled=false` → print `[Gate 4/5] SKIPPED` (no Bash call issued).
  - If both true:
    ```bash
    # [Gate 4/5] Visual check — run_in_background=True
    make visual-check
    ` ` `
    Report: `[Gate 4/5] PASSED` or `[Gate 4/5] FAILED: <stderr>`.
  ```

  **Remove fallback comment:**
  ```
  <!-- fallback: if Agent unavailable → run sequentially: make test-int → make test-e2e → visual check -->
  ```
  Delete this line entirely.

- [ ] **Step 3: Verify**
  ```bash
  grep -n "Agent(" commands/zie-release.md
  ```
  Must return zero matches across the entire file.
  ```bash
  grep -c "run_in_background=True" commands/zie-release.md
  ```
  Must return ≥3 (one for docs-sync, one for Gate 2, one for Gate 3, one for Gate 4 — 4 total when playwright enabled).
  ```bash
  grep -n "fallback" commands/zie-release.md
  ```
  Must return zero matches (both fallback comments removed).

---

## Task 5: Verification grep pass — confirm AC compliance

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- Zero `Agent(` calls exist in `commands/zie-release.md` for gate sections.
- `run_in_background=True` appears for Gate 2, Gate 3, Gate 4 Bash calls.
- Conditional skip logic for Gate 3 and Gate 4 precedes the Bash call.
- Both fallback comments are gone.

**Files:**
- Read: `commands/zie-release.md`

- [ ] **Step 1: Grep — no Agent() calls (AC1)**
  ```bash
  grep -n "Agent(" commands/zie-release.md
  ```
  Expected: zero output.

- [ ] **Step 2: Grep — run_in_background=True present (AC2, AC3)**
  ```bash
  grep -n "run_in_background=True" commands/zie-release.md
  ```
  Expected: ≥3 lines (docs-sync Bash, Gate 2, Gate 3 conditional, Gate 4 conditional).

- [ ] **Step 3: Confirm conditional guards precede Bash calls (AC4)**
  Read the Gate 3 and Gate 4 sections. Confirm the `playwright_enabled` / `has_frontend` check appears as prose *before* the bash code block — the Bash call is inside the `if true:` branch, not issued unconditionally.

- [ ] **Step 4: Grep — no fallback comments (AC6 proxy)**
  ```bash
  grep -n "fallback" commands/zie-release.md
  ```
  Expected: zero output.

- [ ] **Step 5: Read full file**
  Read `commands/zie-release.md` in full. Confirm:
  - Gate ordering preserved: Pre-Gate-1 → Gate 1 (unit, sequential) → Gates 2–4 (parallel Bash) → Gate 5 (code diff)
  - Failure collection prose still says "do NOT stop at first failure" / collect all results together
  - No regression to sequential-only execution

---

## Completion Checklist

- [ ] T1: All 4 Agent() gate blocks located
- [ ] T2: Pre-Gate-1 docs-sync → inline Bash ✓
- [ ] T3: Gate 2 integration → inline Bash ✓
- [ ] T4: Gates 3 & 4 → conditional inline Bash, fallback comments removed ✓
- [ ] T5: Verification grep pass — zero Agent() calls, ≥3 run_in_background=True ✓
