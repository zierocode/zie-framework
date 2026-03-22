# zie-init Deep Scan & Knowledge Drift Detection — Design Spec

**Date:** 2026-03-23
**Status:** approved

---

## Problem

`/zie-init` on an existing project produces knowledge docs (`PROJECT.md`,
`project/architecture.md`, `project/components.md`, `project/decisions.md`)
filled with placeholder templates. The goal is that initializing
zie-framework on an existing project must be **equivalent to having used
zie-framework from day one** — knowledge docs that are accurate, complete,
and reflect the real current state of the codebase.

Additionally, once initialized, there is no mechanism to detect when the
codebase drifts from the recorded knowledge, leaving docs silently stale.

---

## Approach

**Approach A (selected):** Deep scan via `Agent(Explore)` at init time,
hash stored in `zie-framework/.config`, drift surfaced in `/zie-status`,
resync via new `/zie-resync` command.

---

## Components

| Component | Change |
| --- | --- |
| `commands/zie-init.md` | Add greenfield/existing detection + deep scan path |
| `zie-framework/.config` | Add `knowledge_hash`, `knowledge_synced_at` fields |
| `commands/zie-status.md` | Add drift check against `knowledge_hash` |
| `commands/zie-resync.md` | New command — full rescan + update hash |

---

## Data Flow

### Greenfield vs. Existing Detection

A project is **existing** if any of the following are true:

- Any of these directories exist at project root: `src/`, `app/`, `lib/`,
  `api/`, `hooks/`, `components/`, `routes/`, `models/`, `services/`,
  `pkg/`
- Git history has more than 1 commit (`git rev-list --count HEAD > 1`)

Otherwise: **greenfield** — use templates as before (no change).

### Init (existing project)

```text
/zie-init (existing path)
  1. Print: "Existing project detected. Scanning codebase..."
  2. Invoke Agent(subagent_type=Explore):
       Task: scan every file, return a structured analysis report covering:
         - Architecture pattern and overall structure
         - Every significant component/module (name + one-line purpose)
         - Full tech stack with versions (from config files)
         - Data flow from entry point to response
         - Key constraints or decisions in code/comments/docs
         - Test strategy (runner, coverage areas)
         - Active areas (from git log --name-only -20)
       Exclude: node_modules/, .git/, build/, dist/, .next/,
                __pycache__/, *.pyc, coverage/, zie-framework/
       Return: structured markdown report (not the final docs)
  3. Claude reads the Agent report and drafts:
       - zie-framework/PROJECT.md
       - zie-framework/project/architecture.md
       - zie-framework/project/components.md
       - zie-framework/project/decisions.md
         (only real decisions found; unknowns marked TBD)
  4. Present all four drafts inline in the conversation as
     markdown code blocks. Ask:
       "Does this look accurate? Reply 'yes' to write, or describe
       corrections."
  5. If corrections given → apply → re-present → repeat until user
     replies 'yes' or 'y' (case-insensitive). No iteration limit.
  6. Write all four files to disk
  7. Compute knowledge_hash (see Hash Algorithm)
  8. Update zie-framework/.config:
       "knowledge_hash": "<computed hash>",
       "knowledge_synced_at": "<YYYY-MM-DD>"
```

**Failure handling:** If Agent scan fails or returns empty,
warn user ("Scan failed") and offer two choices:

- Retry the scan
- Fall back to templates (same as greenfield path)

### Drift Detection (every /zie-status)

```text
/zie-status
  → read zie-framework/.config
  → if knowledge_hash missing:
      print "Knowledge : ? no baseline — run /zie-resync"
      skip hash check
  → else:
      recompute hash using same algorithm
      equal   → "Knowledge : ✓ synced (knowledge_synced_at)"
      differs → "Knowledge : ⚠ drift detected — run /zie-resync"
```

`knowledge_synced_at` is display-only — not used in drift logic.

The `Knowledge` line appears in the `/zie-status` output block
immediately after `Brain`, before the ROADMAP section:

```text
│ Brain     : <enabled|disabled>
│ Knowledge : ✓ synced (2026-03-23)
│
│ ROADMAP ── Now  : ...
```

It does not block "Next steps" suggestions — informational only.

### Resync (/zie-resync)

```text
/zie-resync
  1. Print: "Rescanning codebase..."
  2. Invoke Agent(subagent_type=Explore) with same scope as init
  3. Claude drafts updated versions of all four knowledge docs
  4. Present inline drafts → user confirms or corrects → repeat
  5. Overwrite all four knowledge docs on confirm
  6. Recompute + store new knowledge_hash + knowledge_synced_at
```

---

## Hash Algorithm

Compute SHA-256 of sorted concatenation of:

1. **All directory paths** in the project tree (recursively), excluding
   `node_modules/`, `.git/`, `build/`, `dist/`, `.next/`,
   `__pycache__/`, `coverage/`, `zie-framework/`
2. **File count per directory** — catches additions/deletions of files
   within existing dirs without hashing content
3. **Full content** of key config files (whichever exist):
   `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`,
   `go.mod`

**Exact concatenation (in this order, UTF-8 encoded):**

1. All directory paths, sorted lexicographically, joined by `\n`
2. Literal separator `\n---\n`
3. Each directory's file count as `<path>:<count>`, sorted, joined `\n`
4. Literal separator `\n---\n`
5. Content of each found config file, sorted by filename, concatenated

Feed the full string into `hashlib.sha256(...).hexdigest()`.

Rationale: catches new modules (dir changes), file additions/deletions,
and dependency changes — the signals that make knowledge docs outdated.
Does NOT hash source file body content → avoids false positives from
minor edits. Known limitation: semantic changes inside existing files
(e.g. internal API refactor) are not detected. Users can always trigger
`/zie-resync` manually.

The exclusion list is hardcoded (not derived from `.gitignore`) — simpler
and sufficient for the common case. No git hook integration is in scope.

---

## .config Schema Addition

File: `zie-framework/.config` (existing JSON file).

**Merge strategy:** read current JSON, add/overwrite only these two
fields, write back. Never remove or overwrite any other existing fields.

New fields:

```json
{
  "knowledge_hash": "<sha256 hex string, lowercase>",
  "knowledge_synced_at": "<YYYY-MM-DD>"
}
```

Both fields are optional — absence means "no baseline."

---

## Edge Cases

| Case | Handling |
| --- | --- |
| User corrects draft multiple times | No limit — write only after 'yes' |
| Large codebase (slow scan) | Print "Scanning..." before invoking Agent |
| No `knowledge_hash` in `.config` | Shows `? no baseline — run /zie-resync` |
| Minor code edits (comments, etc.) | No drift — hash excludes file body |
| `/zie-resync` on greenfield | Idempotent — fast scan, same result |
| `.config` missing | Recommend re-running `/zie-init` |
| Agent scan fails | Warn + offer retry or template fallback |

---

## Out of Scope

- Auto-resync without user confirmation — knowledge docs are always
  human-approved
- Diff-based partial updates — full rescan only
- Automatic resync on git commit or any git hook integration
- Reading `.gitignore` for exclusion list
- Making the exclusion list user-configurable
