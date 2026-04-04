---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-gitignore-gaps.md
---

# .gitignore Gaps — Design Spec

**Problem:** `.gitignore` does not include `zie-framework/evidence/` or
`.pytest_cache/`, risking accidental commits of local audit data and test
cache noise.

**Approach:** Add both entries to the root `.gitignore`. The `evidence/`
entry is higher priority — audit data is local-only by design and must never
enter repo history.

**Components:**

- `.gitignore` — add two entries
- `commands/zie-init.md` — already creates a `zie-framework/.gitignore`
  with `evidence/` for per-project init; the root repo `.gitignore` also
  needs it for the zie-framework repo itself

**Data Flow:**

Current `.gitignore` contents (4 lines):

```text
__pycache__/
*.pyc
.DS_Store
/tmp/zie-framework-*
```

1. Append to `.gitignore`:

   ```text
   .pytest_cache/
   zie-framework/evidence/
   ```

2. Final `.gitignore`:

   ```text
   __pycache__/
   *.pyc
   .DS_Store
   /tmp/zie-framework-*
   .pytest_cache/
   zie-framework/evidence/
   ```

3. Verify `zie-framework/evidence/` directory does not currently contain any
   tracked files (`git ls-files zie-framework/evidence/` should return empty).

**Edge Cases:**

- `zie-framework/evidence/` may not exist yet — `.gitignore` entry is harmless
  when the directory is absent
- `.pytest_cache/` at any depth — the pattern `.pytest_cache/` without a
  leading `/` will match recursively at any subdirectory level, which is
  correct behaviour
- `make clean` already removes `.pytest_cache/` via `find` — the gitignore
  entry is complementary, not redundant

**Out of Scope:**

- Adding `evidence/` to the `templates/gitignore.template` used by
  `/zie-init` for user projects (already handled: `zie-init.md` creates
  `zie-framework/.gitignore` with `evidence/`)
- Adding `node_modules/` (not relevant for this pure-Python repo)
