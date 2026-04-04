---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-makefile-release-branch.md
---

# Makefile Release Branch Safety Check — Design Spec

**Problem:** `Makefile` `release` target (lines 35–39) proceeds directly to
`git checkout main` and merge/tag without verifying the working tree is clean,
risking a corrupted release tag if run from a dirty branch.

**Approach:** Add a pre-flight guard at the top of the `release` target that
asserts the working tree is clean using `git diff --quiet && git diff --cached
--quiet`. Fail fast with a clear message if the tree is dirty.

**Components:**

- `Makefile` — add pre-flight check to the `release` target

**Data Flow:**

Current `release` target (lines 28–39):

```makefile
release: ## Publish release (usage: make release NEW=1.2.3)
ifndef NEW
    $(error NEW is required — usage: make release NEW=1.2.3)
endif
    sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
    git add .claude-plugin/plugin.json
    git diff --cached --quiet || git commit --amend --no-edit
    git checkout main
    git merge dev --no-ff -m "release: v$(NEW)"
    git tag -a v$(NEW) -m "release v$(NEW)"
    git push origin main --tags
    git checkout dev
```

1. After the `ifndef NEW` block, add a clean-tree check:

   ```makefile
   release: ## Publish release (usage: make release NEW=1.2.3)
   ifndef NEW
       $(error NEW is required — usage: make release NEW=1.2.3)
   endif
       @git diff --quiet && git diff --cached --quiet || \
           (echo "ERROR: Working tree is dirty. Commit or stash changes before releasing." && exit 1)
       @git rev-parse --abbrev-ref HEAD | grep -q "^dev$$" || \
           (echo "ERROR: Must release from 'dev' branch. Currently on: $$(git rev-parse --abbrev-ref HEAD)" && exit 1)
   ```

2. The existing `sed` + `git add` + `git commit --amend` block then proceeds
   only on a clean tree.

3. The branch check (`grep -q "^dev$$"`) prevents accidental release from
   feature branches or main itself.

**Edge Cases:**

- `git diff --quiet` exits non-zero if there are unstaged changes; `git diff
  --cached --quiet` exits non-zero if there are staged changes — both must
  pass for a clean tree
- The `git commit --amend` line later in the target will itself fail on a
  dirty tree if the guard is bypassed; the guard is defence-in-depth
- Makefile `@` prefix suppresses echoing the command but not its output —
  the error message will still print
- Tab indentation required in Makefile (not spaces)

**Out of Scope:**

- Verifying that `dev` is up to date with `origin/dev` (network call;
  adds latency)
- Adding a `dry-run` mode to `make release`
