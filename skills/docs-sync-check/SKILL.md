---
name: docs-sync-check
description: Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk. Returns JSON verdict.
user-invocable: false
context: fork
allowed-tools: Read, Glob
argument-hint: ""
model: haiku
effort: low
---

# docs-sync-check — Living Docs Verification

Verify that `CLAUDE.md` and `README.md` reflect the actual state of commands,
skills, and hooks on disk. Called by `/zie-retro` and `/zie-release` as a
parallel fork.

## Input

`$ARGUMENTS` (optional JSON from caller):

```json
{
  "changed_files": ["commands/zie-foo.md", "skills/bar/SKILL.md"]
}
```

If empty or unparseable: run full check across all commands/skills/hooks.

## Steps

1. **Read CLAUDE.md** (project root) — extract lines mentioning `commands/`,
   `skills/`, `hooks/`. If missing → note in details, set `claude_md_stale: false`.

2. **Read README.md** (project root) — extract commands table if present.
   If missing → note in details, set `readme_stale: false`.

3. **Enumerate actual state**:
   - Glob `commands/*.md` → extract base filenames (strip `.md`).
   - Glob `skills/*/SKILL.md` → extract parent directory names.
   - Glob `hooks/*.py` → extract base filenames (exclude `utils.py`).

4. **Compare** each category: docs vs. actual.
   - `missing_from_docs`: items on disk not mentioned in the doc.
   - `extra_in_docs`: items mentioned in doc but not on disk.

5. **Return JSON**:

```json
{
  "claude_md_stale": false,
  "readme_stale": false,
  "missing_from_docs": [],
  "extra_in_docs": [],
  "details": "CLAUDE.md in sync | README.md in sync"
}
```

Set `claude_md_stale: true` if `missing_from_docs` or `extra_in_docs` has entries
relating to CLAUDE.md; `readme_stale: true` for README.md entries.
