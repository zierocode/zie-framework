---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-chore-git-add-A.md
---

# Lean Chore Git Add -A — Design Spec

**Problem:** `commands/chore.md` Step 4 uses `git add -A && git commit -m "chore: <slug>"`, which stages all untracked files including potentially sensitive files (`.env`, credentials, large binaries), violating the global CLAUDE.md Hard Rules for git staging.

**Approach:** Replace the blanket `git add -A` in `commands/chore.md` Step 4 with a two-step instruction: (1) inspect modified tracked files since the last commit using `git diff --name-only HEAD`, then (2) stage only those files with `git add <files>` and include a pre-commit verification step. This matches how `/release`, `/retro`, `/spec`, `/plan`, and `/backlog` all use targeted `git add`. Also fix `commands/implement.md` Step 4 which similarly uses `git add -A`. Add a structural test asserting `git add -A` does not appear in any `commands/*.md` file (exempt: stop-guard.py nudge hint which is a user-facing string, not an automated command).

**Components:**
- `commands/chore.md` — replace Step 4 `git add -A` with targeted `git add` + pre-commit verification instruction
- `commands/implement.md` — replace Step 4 `git add -A` with targeted `git add` instruction (tracks implementation files + ROADMAP)
- `tests/unit/test_no_git_add_A_in_commands.py` — new structural test asserting no `git add -A` in `commands/*.md`

**Data Flow:**
1. User runs `/chore` — defines chore, does work
2. Step 4 (new): run `git diff --name-only HEAD` to enumerate modified tracked files
3. Stage those specific files: `git add <file1> <file2> ...`
4. Pre-commit verification: run `git status` to confirm only intended files are staged; abort if unexpected files appear
5. Commit: `git commit -m "chore: <slug>"`
6. `/implement` Step 4 (new): stage implementation files + ROADMAP explicitly — `git add <changed-impl-files> zie-framework/ROADMAP.md`

**Edge Cases:**
- Chore touches an untracked file (e.g. new config) — instruction must note: "For new untracked files, use `git add <path>` explicitly; never `git add -A`"
- No files modified (dry-run chore) — `git diff --name-only HEAD` returns empty; skip git add; commit is a no-op or skipped
- `/implement` may have a large number of changed files — instruction uses `git add $(git diff --name-only HEAD)` as shorthand, with a note to review output first
- `stop-guard.py` nudge text contains `git add -A` as an example hint string — this is intentional user-facing text, not an automated command; the structural test must exclude hooks/ and only scan `commands/*.md`

**Out of Scope:**
- Changing `Makefile` `push` target (uses `git add -A` by design — human-invoked, user-visible)
- Changing `templates/Makefile` (same reasoning as Makefile)
- Changing `stop-guard.py` nudge hint text (user-facing example, not automated staging)
- Adding git pre-commit hooks to enforce this at the git level
- Retroactively enforcing targeted adds in `/sprint` or other orchestration commands (those delegate to sub-skills)
