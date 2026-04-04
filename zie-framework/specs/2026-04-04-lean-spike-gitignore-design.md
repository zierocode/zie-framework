---
slug: lean-spike-gitignore
status: draft
created: 2026-04-04
---

# Design: Lean Spike — Auto-gitignore spike-*/

## Problem

`/spike` creates `spike-<slug>/` directories at the repo root with no `.gitignore`
guidance. Users may accidentally `git add .` and commit exploratory throwaway
code that was never intended to be tracked.

## Solution

Add a step in `/spike` Step 1 (Create sandbox) that checks whether `spike-*/`
is already present in `.gitignore` and appends it if missing. The check is
idempotent — running `/spike` multiple times never duplicates the entry. Also
add a brief user-facing note that spike dirs are throwaway and git-ignored.

Concretely, insert the following logic into Step 1 of `commands/spike.md`:

```
After mkdir spike-<slug>/:
- Read .gitignore (if it exists).
- If `spike-*/` is not already a line in .gitignore, append it.
- Print: "[spike] spike-*/ added to .gitignore — spike dirs are throwaway and will not be committed."
- If already present, skip silently.
```

## Components

- `commands/spike.md` — only file changed.

## Acceptance Criteria

- After `/spike` runs, `.gitignore` contains exactly one `spike-*/` line.
- Running `/spike` a second time does not add a duplicate `spike-*/` line.
- If `.gitignore` already contained `spike-*/` before `/spike` ran, no change
  is made and no error is raised.
- The confirmation message is printed only when the line is newly added.
- No other commands or files are modified.
