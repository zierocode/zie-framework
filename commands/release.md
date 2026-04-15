---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /release — Release Gate → Merge dev→main → Tag

<!-- preflight: full -->

> **Context tip:** If called after a long session, run `/compact` first to free context.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (checks Now lane — warns if WIP active).

4. Read `VERSION` → current version
5. Check branch → should be `dev`
6. Verify VERSION non-empty: `cat VERSION` → empty/missing → STOP: "Run `make bump NEW=x.y.z` first"

> **Non-Claude:** Use `/release` directly — NOT `make zie-release` (--agent unavailable)

## ลำดับการตรวจสอบ (ต้องผ่านทุกขั้น)

### Pre-Gate-1: Docs Sync (background)

`Skill(zie-framework:docs-sync-check)` (run_in_background=True if supported). Fallback: print `[zie-framework] docs-sync-check unavailable — skipping`. Manual: `make docs-sync`

Collect result with other gates.

### Gate 1/5: Unit Tests

```bash
make test-fast
```

Must exit 0. On failure → `make test-unit` to confirm; if still fails → STOP: "Gate 1 FAILED: unit tests. Run /fix before releasing."

On pass → spawn Gates 2, 3, 4 in parallel.

### Gates 2-4 (parallel)

| Gate | Command | Pass condition |
| --- | --- | --- |
| Gate 2/5 — Integration | `make test-int` | Exit 0 |
| Gate 3/5 — E2E | `make test-e2e` | Only if `playwright_enabled=true`; else SKIP |
| Gate 4/5 — Visual | `make visual-check` | Only if `has_frontend=true` AND `playwright_enabled=true`; else SKIP |

Each: PASSED | SKIPPED | FAILED: \<stderr>

Collect all results. Any fail → STOP: "Gates failed — fix before releasing."

TODOs/secrets scan (parallel): `grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .`
Secrets found → STOP: "Secrets detected — remove before releasing."

### Gate 5/5: Code Diff

`git diff main..HEAD --stat` — scan for anything unexpected before merging.

## All Gates Passed — Release

| Step | Action |
| --- | --- |
| 1 | **Suggest version bump** — scan `[x]` Now items + git log. Apply semver strictly: **major** = breaking API change; **minor** = ANY new user-visible capability; **patch** = ONLY fix/refactor/chore. Default to minor when in doubt. Display: `Bumped to vX.Y.Z (<CHANGE_TYPE>: <reason>). Override: /release --bump-to=X.Y.Z` |
| 2 | **Bump VERSION** — auto-accept suggestion or use `--bump-to=X.Y.Z` override |
| 3 | **Update ROADMAP.md** — move all `[x]` Now → Done with date + version. Clear Now lane (leave `<!-- -->` comment) |
| 4 | **Cleanup shipped SDLC artifacts** — delete backlog/specs/plans for each shipped slug. Stage deletions in release commit. ADRs are permanent — never cleaned |
| 5 | **Draft CHANGELOG** — `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline --no-merges`. Rewrite into Features/Fixed/Changed. Present for approve/edit. Append to `CHANGELOG.md` |
| 6 | **Pre-flight: uncommitted files** — `git status --short`. Only VERSION, CHANGELOG.md, ROADMAP.md (and project files from `make release`). Implementation files → STOP: "Uncommitted implementation files — clean working tree before release." |
| 7 | **Commit release files** — `git add VERSION CHANGELOG.md zie-framework/ROADMAP.md && git commit -m "release: v<NEW_VERSION>"` |
| 8 | **Publish** — `git checkout main && git merge dev --no-ff -m "release: v${NEW_VERSION}" && git tag -s v${NEW_VERSION} -m "release v${NEW_VERSION}" && git push origin main --tags && make _publish NEW=${NEW_VERSION} && git checkout dev && git merge main && git push origin dev`. Fail → STOP: "Release failed — fix and re-run /release." |
| 9 | **Store in brain** (if `zie_memory_enabled=true`) — recall with tags=[wip, plan], then remember: `"Shipped: <feature> v<NEW_VERSION>. Tasks: N."` tags=[shipped, \<project>] |
| 10 | **Archive** — `make archive` (moves backlog/specs/plans for shipped slugs to `zie-framework/archive/`) |
| 11 | **Auto-run `/retro`** |
| 12 | Print: `Released v<NEW_VERSION>` with gate results, branch, tag info |

→ /retro for retrospective (auto-invoked)