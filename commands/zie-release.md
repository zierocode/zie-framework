---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /zie-release — Release Gate → Merge dev→main → Tag

Full automated release gate. Runs all tests, verifies, bumps version, merges
dev→main, tags, and updates ROADMAP. Nothing ships without passing every gate.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. อ่าน `zie-framework/.config` — ใช้ has_frontend, playwright_enabled เป็น
   context
3. Read `VERSION` → current version.
4. Check current git branch → should be `dev`. Warn if not.
5. Verify `VERSION` file exists and is non-empty:

   ```bash
   cat VERSION
   ```

   Empty or missing → **STOP**: "No VERSION file found. Run `make bump NEW=x.y.z` first."

## ลำดับการตรวจสอบ (ต้องผ่านทุกขั้น)

### ตรวจสอบ: Unit Tests

Print: `[Gate 1/5] Unit Tests`

```bash
make test-unit
```

- Must exit 0. On failure → STOP: "Gate 1 FAILED: unit tests. Run /zie-fix before releasing."
- **On pass:** immediately start Fork: Quality Checks (see section below — runs concurrently with Gates 2/3).

### ตรวจสอบ: Integration Tests

Print: `[Gate 2/5] Integration Tests`

```bash
make test-int
```

- Must exit 0, OR skip if no integration tests exist.
- On failure → STOP. Print: "Gate 2 FAILED: integration tests."

### ตรวจสอบ: E2E Tests (ถ้า playwright_enabled=true)

Print: `[Gate 3/5] E2E Tests`

```bash
make test-e2e
```

- Must exit 0.
- On failure → STOP. Print: "Gate 3 FAILED: e2e tests."
- If `playwright_enabled=false` → skip this gate, note it.

### ตรวจสอบ: Visual (ถ้า has_frontend=true)

Print: `[Gate 4/5] Visual Check`

- If `has_frontend=true` AND `playwright_enabled=true`:
  - E2E gate above already covers this — skip.
- If `has_frontend=true` AND `playwright_enabled=false`:
  - Start dev server → manually verify key pages load, no console errors.
  - Ask Zie to confirm: "Visual check passed? (yes/no)"
  - If no → STOP. Fix and re-run.
- If `has_frontend=false` → skip this gate.

### Quality Checks (background Agents + Bash)

Start **immediately after Gate 1 passes** — do NOT wait before running Gate 2.

**TaskCreate** — create task before launching Agent:

```python
TaskCreate(subject="Check docs sync", description="Check CLAUDE.md/README.md against changed files", activeForm="Checking docs sync")
```

**Invoke simultaneously:**

1. `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True)`
   - prompt: `"Check docs sync for changed files: {changed_files}"`
   - Pass `git diff main..HEAD --name-only` output as the `changed_files` argument.

2. Bash: TODOs and secrets scan (runs in parallel with Agent):

   ```bash
   grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
   ```

   Also check changed files for hardcoded API keys, tokens, or credentials.

**Wait for Agent completion:**

- Wait for docs-sync-check Agent to complete (via task notification or TaskOutput)
- **TaskUpdate** — mark task as "completed" when Agent finishes

Results are collected in the section below after Gate 3 completes.

<!-- fallback: if Agent tool unavailable or subagent_type not found,
     call Skill(zie-framework:docs-sync-check) inline (blocking) -->

### รวมผลลัพธ์ Quality Forks

Print: `[Quality Forks] Collecting results`

Collect results from the parallel forks started after Gate 1:

- **Docs sync**: if `claude_md_stale=true` or `readme_stale=true` → update
  stale docs now, before version bump. If in sync → print "Docs in sync".
  (`CLAUDE.md` and `README.md` must reflect current commands/skills/hooks.)
- **TODOs/secrets**: any hits in new code? Fix or create a tracked backlog
  item before proceeding. Any secrets detected → STOP immediately.
- If either fork did not complete → run inline (blocking) before continuing.

### ตรวจสอบ: Code diff ก่อน merge

Print: `[Gate 5/5] Code Diff`

Run `git diff main..HEAD --stat` and scan for anything unexpected before
merging.

## All Gates Passed — Release

1. **[Step 1/10] Suggest version bump** based on what's in Now lane:
   - Scan `[x]` items in Now + git log since last tag
   - Apply rule (take highest that applies):
     - **major** — breaking change: existing users/callers ต้องแก้ code/config
       ของตัวเองเพื่อ upgrade
     - **minor** — new capability: มีของใหม่ที่ใช้ได้เลย โดยไม่ต้องแก้อะไรเดิม
     - **patch** — no new capability: bug fix, docs, tests, refactor, rename,
       style
   - Present suggestion with reasoning:

     ```text
     Suggested bump: minor
     Reason: Knowledge Architecture adds PROJECT.md + project/* (new feature,
     backward compatible)

     Current: <VERSION> → <suggested new version>
     Confirm? (Enter = accept suggestion / major / minor / patch to override)
     ```

2. **Bump VERSION**:
   - Enter → accept the suggested bump shown above
   - Or read `major|minor|patch` from user override
   - Calculate new version: e.g., `1.0.10` + `patch` → `1.0.11`
   - Write new version to `VERSION`

3. **Update ROADMAP.md** *(before commit)*:
   - Move all `[x]` items from "Now" → "Done" with date and version tag.
   - Clear Now lane (leave `<!-- -->` comment).

4. **Cleanup shipped SDLC artifacts** — for each shipped slug derived from Now lane:
   - Delete `zie-framework/backlog/<slug>.md` (if exists)
   - Delete `zie-framework/specs/*-<slug>-design.md` (glob first match, if exists)
   - Delete `zie-framework/plans/*-<slug>.md` (glob first match, if exists)
   - Stage and include these deletions in the release commit.
   - Rationale: git history preserves all content — working tree contains only
     active work. `zie-framework/decisions/` is never cleaned (ADRs are permanent).

5. **Draft CHANGELOG entry**:
   - Run: `git log $(git describe --tags --abbrev=0 2>/dev/null || git
     rev-list --max-parents=0 HEAD)..HEAD --oneline --no-merges`
   - Rewrite commits เป็นภาษาที่คนอ่านเข้าใจ — ไม่ใช่แค่ copy commit messages:
     - Group เป็น **Features**, **Fixed**, **Changed** (ข้าม group ที่ว่าง)
     - แต่ละ item: อธิบาย *what changed and why it matters*
   - Present draft ให้ Zie approve:

     ```text
     ## v<NEW_VERSION> — YYYY-MM-DD

     ### Features
     - <human-readable description>

     ### Fixed / Changed
     - <human-readable description>

     Approve this CHANGELOG entry? (yes / edit)
     ```

   - **yes** → append section at top of `CHANGELOG.md`
   - **edit** → Zie แก้ text → write → continue

6. **Pre-flight: ตรวจสอบ uncommitted files**:

   ```bash
   git status --short
   ```

   - Release commit ควรมีแค่ 3 ไฟล์: `VERSION`, `CHANGELOG.md`,
     `zie-framework/ROADMAP.md`
     (project-specific files เช่น plugin.json จะถูก commit โดย `make release` ต่อไป)
   - ถ้าเจอ implementation files (hooks/*, tests/*, commands/*) ค้างอยู่ →
     STOP: "Uncommitted feature files found: [list]. These should have been
     committed in a `feat:` commit. Run `git add -A && git commit
     -m "feat: SLUG"` — then re-run /zie-release."
   - ถ้าเจอแค่ docs (CLAUDE.md, README.md) ที่ release gate เพิ่งอัปเดต →
     include ได้ในขั้นถัดไป

7. **Commit release files**:

   ```bash
   git add VERSION CHANGELOG.md zie-framework/ROADMAP.md
   git commit -m "release: v<NEW_VERSION>"
   ```

   *(git add ไม่ error ถ้าไฟล์ไม่ได้ถูกแก้)*

8. **Delegate publish to project**:

   ```bash
   make release NEW=<version>
   ```

   - Exit 0 → proceed.
   - Non-zero → **STOP**. Surface make error. Print: "Release failed —
     fix make release and re-run /zie-release."

9. **Store release in brain** (if `zie_memory_enabled=true`):
   - First READ: Call `mcp__plugin_zie-memory_zie-memory__recall`
     with `project=<project> tags=[wip, plan] feature=<slug> limit=5`
   - Then WRITE: Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Shipped: <feature> v<NEW_VERSION>. Tasks: N. Actual: <vs estimate>." tags=[shipped, <project>, <domain>]`

10. **Auto-run `/zie-retro`**.

11. Print:

    ```text
    Released v<NEW_VERSION>

    Gates: unit ✓ | integration ✓ | e2e ✓|n/a | visual ✓|n/a
    Branch: dev merged → main
    Tag: v<NEW_VERSION>

    /zie-retro running...
    ```

## Notes

- If any gate fails, `make release` is never called — fix and re-run `/zie-release`
- Git ops (merge, tag, push) are delegated to `make release` — project-specific
  version bumping is handled by `_bump-extra` in `Makefile.local`
- ROADMAP update (step 3) happens before the commit so the release commit
  reflects the correct state
