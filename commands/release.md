---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /release — Release Gate → Merge dev→main → Tag

<!-- preflight: full -->

> **Context tip:** If called after a long session (sprint / implement), run `/compact` first to free context before proceeding.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (checks Now lane — warns if WIP active).

4. Read `VERSION` → current version
5. Check branch → should be `dev`
6. Verify VERSION non-empty: `cat VERSION` → empty/missing → STOP: "Run `make bump NEW=x.y.z` first"

> **Non-Claude:** Use `/release` directly — NOT `make zie-release` (--agent unavailable)

## ลำดับการตรวจสอบ (ต้องผ่านทุกขั้น)

### Pre-Gate-1: Docs Sync (background)

Run docs-sync check before unit tests — invoke `Skill(zie-framework:docs-sync-check)` (run_in_background=True if supported).
Fallback: if Skill unavailable → print `[zie-framework] docs-sync-check unavailable — skipping`. Manual check: `make docs-sync`

Collect result with other gate results (see "Collect Parallel Gate Results" below).

### ตรวจสอบ: Unit Tests

Print: `[Gate 1/5] Unit Tests`

```bash
make test-fast
```

- Must exit 0. On failure → run `make test-unit` (full suite) to confirm; if still fails → STOP: "Gate 1 FAILED: unit tests. Run /fix before releasing."
- **On pass:** immediately spawn Gates 2, 3, 4 in parallel (see next section).

### ตรวจสอบ: Parallel Gates 2–4

Gate 1 pass → spawn Gates 2, 3, 4 in parallel (`run_in_background=True`):

**Gate 2/5 — Integration tests:**
```bash
make test-int
```
Report: `[Gate 2/5] PASSED` | `[Gate 2/5] SKIPPED` | `[Gate 2/5] FAILED: <stderr>`

**Gate 3/5 — E2E tests (if playwright_enabled=true):** `make test-e2e`
**Gate 4/5 — Visual check (if has_frontend=true AND playwright_enabled=true):** `make visual-check`

Each: PASSED | SKIPPED | FAILED: <stderr>

### Collect Parallel Gate Results

Wait for all three Bash calls. Collect all results:
- All pass/skip → continue
- Any fail → print all failures, STOP: "Gates failed — fix before releasing."

Docs-sync: PASSED → "Docs in sync" | FAILED → update docs | unavailable → skip + `make docs-sync`

TODOs/secrets scan (parallel): `grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .`
Secrets found → STOP: "Secrets detected — remove before releasing."

### ตรวจสอบ: Code diff ก่อน merge

Print: `[Gate 5/5] Code Diff`

Run `git diff main..HEAD --stat` and scan for anything unexpected before
merging.

## All Gates Passed — Release

<!-- NOTE: version suggestion requires judgment about breaking changes. -->
1. **[Step 1/10] Suggest version bump** — scan `[x]` Now items + git log. Apply semver strictly:
   - **major**: breaking change to API/config/command behavior
   - **minor**: ANY new user-visible capability (new command, skill, flag, hook, template) — even one
   - **patch**: ONLY when ALL items are fix/refactor/chore/docs with zero new user-facing surface

   Default to **minor** whenever in doubt between minor and patch. Reset patch to 0 on minor bump.
   Display: `Bumped to vX.Y.Z (CHANGE_TYPE: <reason>). Send override if wrong. Override: /release --bump-to=X.Y.Z`

2. **Bump VERSION**: auto-accept suggestion or use `--bump-to=X.Y.Z` override. Write to `VERSION`.

3. **Update ROADMAP.md** *(before commit)*:
   - Move all `[x]` items from "Now" → "Done" with date and version tag.
   - Clear Now lane (leave `<!-- -->` comment).

4. **Cleanup shipped SDLC artifacts** — delete `backlog/<slug>.md`, `specs/*-<slug>-design.md`, `plans/*-<slug>.md` for each shipped slug. Stage deletions in release commit. (ADRs permanent — never cleaned.)

<!-- NOTE: narrative rewrite produces human-readable commit history. -->
5. **Draft CHANGELOG entry**: run `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline --no-merges`. Rewrite into Features/Fixed/Changed groups. Present for approve/edit. On `yes` → append to `CHANGELOG.md`; on `edit` → apply changes → write.

6. **Pre-flight: ตรวจสอบ uncommitted files**: run `git status --short`. Release commit should have only `VERSION`, `CHANGELOG.md`, `ROADMAP.md` (project files like `plugin.json` committed by `make release`). Implementation files found → STOP: "Uncommitted implementation files — clean working tree before release." Docs from this gate → include.

7. **Commit release files**:
   ```bash
   git add VERSION CHANGELOG.md zie-framework/ROADMAP.md
   git commit -m "release: v<NEW_VERSION>"
   ```

8. **Publish release** (do NOT call `make release` — do git ops directly):
   ```bash
   git checkout main && git merge dev --no-ff -m "release: v${NEW_VERSION}"
   git tag -s v${NEW_VERSION} -m "release v${NEW_VERSION}"
   git push origin main --tags
   make _publish NEW=${NEW_VERSION}
   git checkout dev && git merge main && git push origin dev
   ```
   Fail → STOP: "Release failed — fix and re-run /release."

9. **Store release in brain** (if `zie_memory_enabled=true`):
   - First READ: Call `mcp__plugin_zie-memory_zie-memory__recall`
     with `project=<project> tags=[wip, plan] feature=<slug> limit=5`
   - Then WRITE: Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Shipped: <feature> v<NEW_VERSION>. Tasks: N. Actual: <vs estimate>." tags=[shipped, <project>, <domain>]`

10. **Archive**: `make archive` — moves backlog/specs/plans for shipped slugs to `zie-framework/archive/`.

11. **Auto-run `/retro`**.

12. Print:
    ```text
    Released v<NEW_VERSION>

    Gates: unit ✓ | integration ✓ | e2e ✓|n/a | visual ✓|n/a
    Branch: dev merged → main
    Tag: v<NEW_VERSION>

    /retro running...
    ```

→ /retro for retrospective (auto-invoked)

