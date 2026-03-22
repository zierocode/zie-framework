---
description: Full release gate — run all test gates, bump version, merge dev→main, tag, and trigger retrospective.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

# /zie-ship — Release Gate → Merge dev→main → Tag

Full automated release gate. Runs all tests, verifies, bumps version, merges dev→main, tags, and updates ROADMAP. Nothing ships without passing every gate.

## Pre-flight

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → has_frontend, playwright_enabled, test_runner.
3. Read `VERSION` → current version.
4. Check current git branch → should be `dev`. Warn if not.

## Gate Sequence (all must pass)

### Gate 1 — Unit Tests
```
make test-unit
```
- Must exit 0.
- On failure → STOP. Print: "Gate 1 FAILED: unit tests. Run /zie-fix before shipping."

### Gate 2 — Integration Tests
```
make test-int
```
- Must exit 0, OR skip if no integration tests exist.
- On failure → STOP. Print: "Gate 2 FAILED: integration tests."

### Gate 3 — E2E Tests (if `playwright_enabled=true`)
```
make test-e2e
```
- Must exit 0.
- On failure → STOP. Print: "Gate 3 FAILED: e2e tests."
- If `playwright_enabled=false` → skip this gate, note it.

### Gate 4 — Visual Verification (if `has_frontend=true`)
- Invoke `Skill(vercel:agent-browser-verify)` or `Skill(vercel:verification)` if available.
- If not available → manual check: start dev server, describe what to verify, ask Zie to confirm.

### Gate 5 — Verification Checklist
- Invoke `Skill(superpowers:verification-before-completion)`.

### Gate 6 — Code Review
- Invoke `Skill(superpowers:requesting-code-review)` with a subagent.

## All Gates Passed — Release

5. Ask: "All gates passed. Bump version? Current: <VERSION>. Type: patch | minor | major"

6. **Bump VERSION**:
   - Read `patch|minor|major` from user response (default: `patch` if Enter pressed)
   - Calculate new version: e.g., `1.0.10` + `patch` → `1.0.11`
   - Write new version to `VERSION`

7. **Update CHANGELOG.md**:
   - Run: `git log $(git describe --tags --abbrev=0)..HEAD --oneline --no-merges`
   - Append new section at top:
     ```
     ## v<NEW_VERSION> — YYYY-MM-DD
     <grouped git log entries by feat/fix/chore>
     ```

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

11. **Store release in brain** (if `zie_memory_enabled=true`):
    - `remember "Released v<NEW_VERSION> of <project>. Changes: <brief>." priority=project tags=[release, v<NEW_VERSION>] project=<project>`

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
