---
name: zie-framework:docs-sync
description: Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk. Returns JSON verdict.
user-invocable: false
context: fork
allowed-tools: Read, Glob
argument-hint: "[changed_files]"
model: haiku
effort: low
---

# docs-sync — Living Docs Verification

Verify that `CLAUDE.md`, `README.md`, and `PROJECT.md` reflect the actual state of commands, skills, and hooks on disk. Called by `/retro` and `/release` as a parallel fork.

## Input

`$ARGUMENTS` (optional JSON from caller):

```json
{
  "changed_files": ["commands/zie-foo.md", "skills/bar/SKILL.md"]
}
```

Empty/unparseable → run full check across all commands/skills/hooks.

## Execution

```bash
python3 "${CLAUDE_SKILL_DIR}/run.py"
```

Pass `$ARGUMENTS` as the first command-line argument if provided.

## Steps (for reference)

1. **Read CLAUDE.md** (project root) — extract lines mentioning `commands/`, `skills/`, `hooks/`. Missing → note in details, set `claude_md_stale: false`.

2. **Read README.md** (project root) — extract commands table if present. Missing → note in details, set `readme_stale: false`.

3. **Enumerate actual state**:
   - Glob `commands/*.md` → extract base filenames (strip `.md`).
   - Glob `skills/*/SKILL.md` → extract parent directory names.
   - Glob `hooks/*.py` → extract base filenames (exclude `utils.py`).

3b. **Read PROJECT.md** — parse Commands and Skills tables:
    - Read `PROJECT.md` at project root. Missing → set `project_md_stale: false`, append "PROJECT.md not found — skipped" to `details`, skip cross-reference.
    - Extract Commands table: every `| /command |` row. Skip headers (`| Command |`, `| --- |`). Strip leading `/` from names. Strip `.md` suffix from disk basenames before comparing.
    - Extract Skills table: every `| skill-name |` row. Skip headers. Skill names are bare (no path prefix).
    - Absent Commands/Skills table → treat as empty (all disk items → `missing_from_project_md`).
    - Cross-reference:
      - `missing_from_project_md`: on disk but NOT in PROJECT.md tables.
      - `extra_in_project_md`: in PROJECT.md tables but NOT on disk.
    - Set `project_md_stale: true` if either list non-empty; `false` otherwise.

4. **Compare** each category: docs vs. actual.
   - `missing_from_docs`: on disk not mentioned in doc.
   - `extra_in_docs`: in doc but not on disk.

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
| `claude_md_stale` | CLAUDE.md doesn't mention commands/skills/hooks directories |
| `readme_stale` | README.md commands table doesn't match disk |
| `project_md_stale` | PROJECT.md tables don't match disk |
| `missing_from_docs` | On disk but not documented in README.md |
| `extra_in_docs` | Documented but not on disk (deleted?) |
| `missing_from_project_md` | On disk but not in PROJECT.md tables |
| `extra_in_project_md` | In PROJECT.md but not on disk |

`claude_md_stale: true` if `missing_from_docs`/`extra_in_docs` has CLAUDE.md entries; `readme_stale: true` for README.md entries.