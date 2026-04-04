# Implementation Plan: zie-status Git Velocity Cache

**Slug:** `zie-status-git-velocity-cache`
**Spec:** `zie-framework/specs/2026-04-04-zie-status-git-velocity-cache-design.md`
**Date:** 2026-04-04
**WIP:** 1

## Overview

Replace the multi-call velocity loop in `commands/zie-status.md` with a single
`git log` command. Markdown-only change.

## Steps

### 1. Read current step 6 in `commands/zie-status.md`

- Read lines 63–76 to capture exact wording before editing.

### 2. Replace step 6 — velocity computation

Edit `commands/zie-status.md` step 6. Replace:

```
git tag --sort=-version:refname | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | head -6
```

…plus the per-tag `git log -1 --format=%ai <tag>` loop instruction with:

```bash
git log --tags --simplify-by-decoration --pretty="%D|%ai" | \
  grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
```

New prose for step 6:

> **Compute release velocity** via a single Bash call:
>
> ```bash
> git log --tags --simplify-by-decoration --pretty="%D|%ai" | \
>   grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
> ```
>
> Each output line contains ref decorations and ISO author-date separated by
> `|`. Parse the first semver tag (`v?X.Y.Z`) and the date (`YYYY-MM-DD`) from
> each line.
>
> - Collect up to 6 entries (to compute up to 5 intervals).
> - For each consecutive pair, compute `days = (date[n] - date[n+1]).days`.
> - Fewer than 2 entries → velocity string = `"Velocity: not enough releases yet"`.
> - Otherwise → `"Velocity (last N): Xd, Yd, Zd, …"` where N = number of intervals (≤ 5).

### 3. Verify no test regressions

```bash
make test-fast
```

Confirm all existing `/zie-status` tests pass (output format, section
presence, velocity string pattern).

### 4. Lint

```bash
make lint
```

No Python changes expected — lint should be clean.

## Acceptance Check

| AC | Verified by |
| --- | --- |
| AC-1 — 1 Bash call | Code review: count Bash fences in step 6 |
| AC-2 — format unchanged | `make test-fast` |
| AC-3 — not-enough-releases path | `make test-fast` |
| AC-4 — markdown-only | `git diff --name-only` shows only `commands/zie-status.md` |
| AC-5 — existing tests pass | `make test-fast` green |

## Rollback

Revert the single edit to `commands/zie-status.md`. No migrations, no config,
no hook changes.
