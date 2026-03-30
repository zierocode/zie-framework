---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: haiku
effort: medium
---

# /zie-release — Release Gate → Merge dev→main → Tag

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

### Pre-Gate-1: Docs Sync (background)

Spawn docs-sync-check before unit tests — runs concurrently:

```python
TaskCreate(subject="Check docs sync", description="Check CLAUDE.md/README.md against changed files", activeForm="Checking docs sync")
Agent(subagent_type="general-purpose", run_in_background=True, prompt="Check CLAUDE.md and README.md for staleness. (1) Scan zie-framework/commands/*.md — extract all /zie-* command names. (2) Scan zie-framework/skills/*/*.md — extract all skill names. (3) Scan zie-framework/hooks/*.py — extract hook event types. (4) Check CLAUDE.md Development Commands section lists all commands. (5) Check README.md skills table lists all skills. Report: [docs-sync] PASSED or [docs-sync] FAILED: <what's stale>. Return JSON: { 'in_sync': bool, 'missing_from_docs': [...], 'extra_in_docs': [...], 'details': str }")
```

<!-- fallback: if Agent unavailable → print `[zie-framework] docs-sync-check unavailable — skipping` and continue. Manual check: make docs-sync -->

### ตรวจสอบ: Unit Tests

Print: `[Gate 1/5] Unit Tests`

```bash
make test-fast
```

- Must exit 0. On failure → run `make test-unit` (full suite) to confirm; if still fails → STOP: "Gate 1 FAILED: unit tests. Run /zie-fix before releasing."
- **On pass:** immediately spawn Gates 2, 3, 4 in parallel (see next section).

### ตรวจสอบ: Parallel Gates 2–4

Upon Gate 1 success, immediately spawn three Agents simultaneously:

```python
Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run integration tests: execute `make test-int`. Report result: [Gate 2/5] PASSED or [Gate 2/5] FAILED: <reason>. If no integration tests exist, report [Gate 2/5] SKIPPED.")

Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run e2e tests if enabled: check playwright_enabled in zie-framework/.config. If true, execute `make test-e2e`. If false, skip. Report: [Gate 3] PASSED or [Gate 3] SKIPPED or [Gate 3] FAILED: <reason>.")

Agent(subagent_type="general-purpose", run_in_background=True, prompt="Visual check if applicable: check has_frontend and playwright_enabled in zie-framework/.config. If has_frontend=true and playwright_enabled=false, start dev server and verify key pages load without console errors. Report: [Gate 4] PASSED or [Gate 4] SKIPPED or [Gate 4] FAILED: <reason>.")
```

<!-- fallback: if Agent unavailable → run sequentially: make test-int → make test-e2e → visual check -->

### Collect Parallel Gate Results

Wait for all three gate Agents to complete. Collect results from each (do NOT stop at first failure):

- If all three pass (or skip) → print "Gates 2, 3, 4 PASSED" → continue
- If any fail → print all failures together, then STOP before version bump:
  ```
  [Gate 2] FAILED: integration tests failed
  [Gate 3] FAILED: e2e tests timed out
  ```
- Also collect docs-sync-check result (Pre-Gate-1 Agent):
  - `[docs-sync] PASSED` → print "Docs in sync"
  - `[docs-sync] FAILED` → update stale docs now before version bump
  - Not yet complete → wait for it (non-critical: does not block release if unavailable)

Also run TODOs and secrets scan (Bash, parallel with gate agents):

```bash
grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
```

Any secrets detected → STOP immediately.

### รวมผลลัพธ์ Quality Forks

Print: `[Quality Forks] Collecting results`

All parallel results collected in "Collect Parallel Gate Results" above.
This section confirms before proceeding to version bump:

- Gates 2, 3, 4: all PASSED or SKIPPED → continue
- Docs sync: stale docs updated if needed → continue
- TODOs/secrets: no secrets detected → continue

### ตรวจสอบ: Code diff ก่อน merge

Print: `[Gate 5/5] Code Diff`

Run `git diff main..HEAD --stat` and scan for anything unexpected before
merging.

## All Gates Passed — Release

<!-- model: sonnet reasoning: version suggestion compares commits against semver rules and requires judgment about breaking changes vs new features. -->
1. **[Step 1/10] Suggest version bump** — scan `[x]` Now items + git log. Apply: major (breaking change), minor (new capability), patch (fix/docs/refactor). Display:
   `Bumped to vX.Y.Z (CHANGE_TYPE). Send override if wrong. Override: /zie-release --bump-to=X.Y.Z`

2. **Bump VERSION**: auto-accept suggestion or use `--bump-to=X.Y.Z` override. Write to `VERSION`.

3. **Update ROADMAP.md** *(before commit)*:
   - Move all `[x]` items from "Now" → "Done" with date and version tag.
   - Clear Now lane (leave `<!-- -->` comment).

4. **Cleanup shipped SDLC artifacts** — delete `backlog/<slug>.md`, `specs/*-<slug>-design.md`, `plans/*-<slug>.md` for each shipped slug. Stage deletions in release commit. (ADRs permanent — never cleaned.)

<!-- model: sonnet reasoning: narrative rewrite of commit messages into human-readable feature/fix groups requires editorial judgment and understanding of change impact. -->
5. **Draft CHANGELOG entry**: run `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline --no-merges`. Rewrite into Features/Fixed/Changed groups. Present for approve/edit. On `yes` → append to `CHANGELOG.md`; on `edit` → apply changes → write.

6. **Pre-flight: ตรวจสอบ uncommitted files**: run `git status --short`. Release commit should have only `VERSION`, `CHANGELOG.md`, `ROADMAP.md` (project files like `plugin.json` committed by `make release`). Implementation files found → STOP. Docs from this gate → include.

7. **Commit release files**:

   ```bash
   git add VERSION CHANGELOG.md zie-framework/ROADMAP.md
   git commit -m "release: v<NEW_VERSION>"
   ```

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

10. **Archive**: `make archive` — moves backlog/specs/plans for shipped slugs to `zie-framework/archive/`.

11. **Auto-run `/zie-retro`**.

12. Print:

    ```text
    Released v<NEW_VERSION>

    Gates: unit ✓ | integration ✓ | e2e ✓|n/a | visual ✓|n/a
    Branch: dev merged → main
    Tag: v<NEW_VERSION>

    /zie-retro running...
    ```

