---
name: docs-sync-check
description: Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk. Returns JSON verdict.
user-invocable: false
context: fork
allowed-tools: Read, Glob
argument-hint: "[changed_files]"
model: haiku
effort: low
---

# docs-sync-check — Living Docs Verification

Verify that `CLAUDE.md` and `README.md` reflect the actual state of commands,
skills, and hooks on disk. Called by `/retro` and `/release` as a
parallel fork.

## Input

`$ARGUMENTS` (optional JSON from caller):

```json
{
  "changed_files": ["commands/zie-foo.md", "skills/bar/SKILL.md"]
}
```

If empty or unparseable: run full check across all commands/skills/hooks.

## Execution

Run the Python script:

```bash
python3 "${CLAUDE_SKILL_DIR}/run.py"
```

Pass `$ARGUMENTS` as the first command-line argument if provided.

## Steps (for reference)

1. **Read CLAUDE.md** (project root) — extract lines mentioning `commands/`,
   `skills/`, `hooks/`. If missing → note in details, set `claude_md_stale: false`.

2. **Read README.md** (project root) — extract commands table if present.
   If missing → note in details, set `readme_stale: false`.

3. **Enumerate actual state**:
   - Glob `commands/*.md` → extract base filenames (strip `.md`).
   - Glob `skills/*/SKILL.md` → extract parent directory names.
   - Glob `hooks/*.py` → extract base filenames (exclude `utils.py`).

3b. **Read PROJECT.md** — parse Commands and Skills tables:
    - Read `PROJECT.md` at the project root. If missing → set `project_md_stale: false`,
      append "PROJECT.md not found — skipped" to `details`, skip cross-reference.
    - Extract Commands table: every `| /command |` row. Skip header rows
      (`| Command |`, `| --- |`). Strip the leading `/` from each command name.
      Strip `.md` suffix from disk basenames before comparing.
    - Extract Skills table: every `| skill-name |` row. Skip header rows
      (`| Skill |`, `| --- |`). Skill names are bare (no path prefix).
    - If a Commands or Skills table is absent from PROJECT.md, treat as empty
      (all disk items → `missing_from_project_md`).
    - Cross-reference:
      - `missing_from_project_md`: commands/skills on disk NOT in PROJECT.md tables.
      - `extra_in_project_md`: entries in PROJECT.md tables NOT found on disk.
    - Set `project_md_stale: true` if either list is non-empty; `false` otherwise.

4. **Compare** each category: docs vs. actual.
   - `missing_from_docs`: items on disk not mentioned in the doc.
   - `extra_in_docs`: items mentioned in doc but not on disk.

5. **Return JSON**:

```json
{
  "claude_md_stale": false,
  "readme_stale": false,
  "project_md_stale": false,
  "missing_from_docs": [],
  "extra_in_docs": [],
  "missing_from_project_md": [],
  "extra_in_project_md": [],
  "details": "CLAUDE.md in sync | README.md in sync | PROJECT.md in sync"
}
```

## Interpretation

| Field | Meaning |
| --- | --- |
| `claude_md_stale` | true if CLAUDE.md doesn't mention commands/skills/hooks directories |
| `readme_stale` | true if README.md commands table doesn't match disk |
| `project_md_stale` | true if PROJECT.md tables don't match disk |
| `missing_from_docs` | Items on disk but not documented in README.md |
| `extra_in_docs` | Items documented but not on disk (deleted?) |
| `missing_from_project_md` | Items on disk but not in PROJECT.md tables |
| `extra_in_project_md` | Items in PROJECT.md but not on disk |

Set `claude_md_stale: true` if `missing_from_docs` or `extra_in_docs` has entries
relating to CLAUDE.md; `readme_stale: true` for README.md entries.
