---
tags: [chore]
---

# quality-gate: Scope Bandit Scan to Staged Files Only

## Problem

`hooks/quality-gate.py` runs `bandit` on up to 20 Python files selected by
`rglob("*.py")` from the entire repo — not scoped to the files being committed.
This means a commit touching one hook file triggers a security scan of 20
arbitrary Python files, many of which may be unrelated to the change and
already scanned in a previous commit.

## Motivation

Scoping bandit to staged Python files only (`git diff --cached --name-only`)
makes the scan directly relevant to the commit, reduces noise from pre-existing
issues in unrelated files, and improves performance on large repos. The existing
20-file cap is replaced by "all staged Python files" (naturally bounded to what's
actually being committed).

## Rough Scope

- Replace `list(cwd.rglob("*.py"))[:20]` with output of
  `git diff --cached --name-only --diff-filter=ACM` filtered to `.py` files
- If `git diff` fails or returns empty → fall back silently (skip bandit scan)
- Filter out venv/.venv/node_modules as before
- Update tests: staged files path tested; empty-staged-files path exits cleanly
