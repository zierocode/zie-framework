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
5. **Version Consistency Gate** — before running any tests, verify that `VERSION`
   and `.claude-plugin/plugin.json` are in sync:

   ```bash
   VERSION_VAL=$(cat VERSION)
   PLUGIN_VAL=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
   if [ "$VERSION_VAL" != "$PLUGIN_VAL" ]; then
     echo "Version mismatch: VERSION=$VERSION_VAL, plugin.json=$PLUGIN_VAL — run \`make bump NEW=<v>\` to sync before releasing."
     exit 1
   fi
   ```

   - Exit 0 (versions match) → continue.
   - Exit 1 (mismatch) → **STOP**. Print the error message from the script
     and do not proceed to test gates.

## ลำดับการตรวจสอบ (ต้องผ่านทุกขั้น)

### ตรวจสอบ: Unit Tests

Print: `[Gate 1/7] Unit Tests`

```bash
make test-unit
```

- Must exit 0. On failure → STOP: "Gate 1 FAILED: unit tests. Run /zie-fix before releasing."

### ตรวจสอบ: Integration Tests

Print: `[Gate 2/7] Integration Tests`

```bash
make test-int
```

- Must exit 0, OR skip if no integration tests exist.
- On failure → STOP. Print: "Gate 2 FAILED: integration tests."

### ตรวจสอบ: E2E Tests (ถ้า playwright_enabled=true)

Print: `[Gate 3/7] E2E Tests`

```bash
make test-e2e
```

- Must exit 0.
- On failure → STOP. Print: "Gate 3 FAILED: e2e tests."
- If `playwright_enabled=false` → skip this gate, note it.

### ตรวจสอบ: Visual (ถ้า has_frontend=true)

Print: `[Gate 4/7] Visual Check`

- If `has_frontend=true` AND `playwright_enabled=true`:
  - E2E gate above already covers this — skip.
- If `has_frontend=true` AND `playwright_enabled=false`:
  - Start dev server → manually verify key pages load, no console errors.
  - Ask Zie to confirm: "Visual check passed? (yes/no)"
  - If no → STOP. Fix and re-run.
- If `has_frontend=false` → skip this gate.

### ตรวจสอบ: TODOs และ Secrets

Print: `[Gate 5/7] TODOs and Secrets`

- Scan for leftover stubs:

  ```bash
  grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
  ```

  Any hits in new code? Fix or create a tracked backlog item before
  proceeding.

- Scan for hardcoded secrets in changed files: no API keys, tokens,
  passwords, or credentials in any file being committed.

### ตรวจสอบ: Docs sync

Print: `[Gate 6/7] Docs Sync`

Scan `git diff main..HEAD --name-only` → ถ้ามี new/changed commands, skills,
hooks, or project structure:

- `CLAUDE.md` — project structure + tech stack ยังถูกต้องไหม?
- `README.md` — commands table + pipeline section ยังถูกต้องไหม?
- `zie-framework/PROJECT.md` — commands/skills/hooks list ยังถูกต้องไหม?

ถ้า out of sync → อัปเดตก่อน commit

### ตรวจสอบ: Code diff ก่อน merge

Print: `[Gate 7/7] Code Diff`

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

4. **Draft CHANGELOG entry**:
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

5. **Pre-flight: ตรวจสอบ uncommitted files**:

   ```bash
   git status --short
   ```

   - Release commit ควรมีแค่ 4 ไฟล์: `VERSION`, `CHANGELOG.md`,
     `zie-framework/ROADMAP.md`, `.claude-plugin/plugin.json`
   - ถ้าเจอ implementation files (hooks/*, tests/*, commands/*) ค้างอยู่ →
     STOP: "Uncommitted feature files found: [list]. These should have been
     committed in a `feat:` commit. Run `git add -A && git commit
     -m "feat: SLUG"` — then re-run /zie-release."
   - ถ้าเจอแค่ docs (CLAUDE.md, README.md) ที่ release gate เพิ่งอัปเดต →
     include ได้ในขั้นถัดไป

6. **Commit release files**:

   ```bash
   git add VERSION CHANGELOG.md zie-framework/ROADMAP.md \
     .claude-plugin/plugin.json
   git commit -m "release: v<NEW_VERSION>"
   ```

   *(git add ไม่ error ถ้าไฟล์ไม่ได้ถูกแก้)*

7. **Readiness gate — verify `make release` is implemented**:

   ```bash
   grep -q "ZIE-NOT-READY" Makefile && echo "NOT_READY" || echo "READY"
   ```

   - `NOT_READY` → **STOP**. Print:

     ```text
     Release blocked: make release is not implemented yet.

     Open Makefile, replace the ZIE-NOT-READY skeleton with real
     publish steps for this project, then re-run /zie-release.
     ```

   - `READY` → proceed.

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
- Git ops (merge, tag, push) are delegated to `make release` — implement
  the skeleton in your project's Makefile before first release
- ROADMAP update (step 3) happens before the commit so the release commit
  reflects the correct state
