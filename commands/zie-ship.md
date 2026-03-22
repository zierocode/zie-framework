---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

# /zie-ship — Release Gate → Merge dev→main → Tag

Full automated release gate. Runs all tests, verifies, bumps version, merges dev→main, tags, and updates ROADMAP. Nothing ships without passing every gate.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. อ่าน `zie-framework/.config` — ใช้ has_frontend, playwright_enabled เป็น context
3. Read `VERSION` → current version.
4. Check current git branch → should be `dev`. Warn if not.

## ลำดับการตรวจสอบ (ต้องผ่านทุกขั้น)

### ตรวจสอบ: Unit Tests
```
make test-unit
```
- Must exit 0.
- On failure → STOP. Print: "Gate 1 FAILED: unit tests. Run /zie-fix before shipping."

### ตรวจสอบ: Integration Tests
```
make test-int
```
- Must exit 0, OR skip if no integration tests exist.
- On failure → STOP. Print: "Gate 2 FAILED: integration tests."

### ตรวจสอบ: E2E Tests (ถ้า playwright_enabled=true)
```
make test-e2e
```
- Must exit 0.
- On failure → STOP. Print: "Gate 3 FAILED: e2e tests."
- If `playwright_enabled=false` → skip this gate, note it.

### ตรวจสอบ: Visual (ถ้า has_frontend=true)
- Invoke `Skill(vercel:agent-browser-verify)` or `Skill(vercel:verification)` if available.
- If not available → manual check: start dev server, describe what to verify, ask Zie to confirm.

### ตรวจสอบ: Checklist ก่อน release
- Invoke `Skill(zie-framework:verify)`.

### ตรวจสอบ: Docs sync
- Scan `git diff main..HEAD --name-only` → ถ้ามี new commands, skills, hooks, หรือ project structure เปลี่ยน:
  - `CLAUDE.md` — project structure + tech stack ยังถูกต้องไหม?
  - `README.md` — directory structure + commands table ยังถูกต้องไหม?
- ถ้า out of sync → อัปเดตก่อน merge

### ตรวจสอบ: Code diff ก่อน merge
- Run `git diff main..HEAD --stat` and scan for anything unexpected before merging.

## All Gates Passed — Release

5. **Suggest version bump** based on what's in Now lane:
   - Scan `[x]` items in Now + git log since last tag
   - Apply rule (take highest that applies):
     - **major** — breaking change: existing users/callers ต้องแก้ code/config ของตัวเองเพื่อ upgrade
     - **minor** — new capability: มีของใหม่ที่ใช้ได้เลย โดยไม่ต้องแก้อะไรเดิม
     - **patch** — no new capability: bug fix, docs, tests, refactor, rename, style
   - Present suggestion with reasoning:
     ```
     Suggested bump: minor
     Reason: Knowledge Architecture adds PROJECT.md + project/* (new feature, backward compatible)

     Current: <VERSION> → <suggested new version>
     Confirm? (Enter = accept / major / minor / patch to override)
     ```

6. **Bump VERSION**:
   - Read `patch|minor|major` from user response (default: `patch` if Enter pressed)
   - Calculate new version: e.g., `1.0.10` + `patch` → `1.0.11`
   - Write new version to `VERSION`

7. **Draft CHANGELOG entry**:
   - Run: `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline --no-merges`
   - Rewrite commits เป็นภาษาที่คนอ่านเข้าใจ — ไม่ใช่แค่ copy commit messages:
     - Group เป็น **Features**, **Fixed**, **Changed** (ข้าม group ที่ว่าง)
     - แต่ละ item: อธิบาย *what changed and why it matters* ไม่ใช่แค่ชื่อ commit
   - Present draft ให้ Zie approve:
     ```
     ## v<NEW_VERSION> — YYYY-MM-DD

     ### Features
     - <human-readable description>

     ### Fixed / Changed
     - <human-readable description>

     Approve this CHANGELOG entry? (yes / edit)
     ```
   - **yes** → append section at top of `CHANGELOG.md` (สร้างไฟล์ถ้ายังไม่มี)
   - **edit** → Zie แก้ text → write → continue

8. **Commit release files**:
   ```
   git add VERSION CHANGELOG.md zie-framework/ROADMAP.md
   git commit -m "release: v<NEW_VERSION>"
   ```

9. **Merge to main**:
   ```
   git checkout main
   git merge dev --no-ff -m "release: v<NEW_VERSION>"
   git tag -a v<NEW_VERSION> -m "release v<NEW_VERSION>"
   git push origin main --tags
   git checkout dev
   ```

10. **Update ROADMAP.md**:
    - Move all items from "Now" section → "Done" section with date and version.
    - Re-prioritize "Next" section if needed.

10b. If `zie_memory_enabled=true` — READ before writing ship memory:
    - Single batch query: `recall project=<project> tags=[wip, plan] feature=<slug> limit=5`
    - Returns WIP notes + plan estimate → compute actual vs estimated complexity.

11. **Store release in brain** (if `zie_memory_enabled=true`):
    - `remember "Shipped: <feature> v<NEW_VERSION>. Tasks: N. Actual: <vs estimate>." tags=[shipped, <project>, <domain>]`

12. **Auto-run `/zie-retro`**.

13. Print:
    ```
    Released v<NEW_VERSION>

    Gates: unit ✓ | integration ✓ | e2e ✓|n/a | visual ✓|n/a
    Branch: dev merged → main
    Tag: v<NEW_VERSION>

    /zie-retro running...
    ```

## Notes
- Never call `make ship` directly — always go through `/zie-ship` for the full gate sequence
- If any gate fails, no code is merged — fix and re-run `/zie-ship`
- The merge happens last, after all gates pass
