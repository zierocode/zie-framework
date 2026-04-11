# Backlog: Fix /chore to use targeted git add instead of git add -A

**Problem:**
commands/chore.md Step 4 specifies: `git add -A && git commit -m "chore: <slug>"`.
`git add -A` stages all changes including untracked files, which violates the global
CLAUDE.md Hard Rules: "can accidentally include sensitive files (.env, credentials)
or large binaries". /chore is a quick maintenance track where the staged files are
known ahead of time.

**Motivation:**
Security + consistency with CLAUDE.md hard rules. /chore users run this on "quick
doc edits, config tweaks, version bumps" — the files modified are well-defined and
should be staged explicitly. A blanket `git add -A` in an automated track is risky.

**Rough scope:**
- Replace `git add -A` with `git add <specific files changed in this chore>`
  or provide guidance to stage specific files before committing
- Add a pre-commit check instruction: "verify only intended files are staged"
- Align with how /release and /retro handle commits (both use targeted adds)
- Tests: structural test asserting no `git add -A` in command files
