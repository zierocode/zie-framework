---
description: Rescan codebase and update knowledge docs + knowledge hash. Run when drift detected or after major structural changes.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Agent
model: sonnet
effort: medium
---

# /resync — Rescan Codebase + Update Knowledge Docs

Full rescan of project codebase. Updates PROJECT.md, project/architecture.md,
project/components.md, project/context.md, and knowledge_hash in .config.
All updates require user confirmation before writing.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Check `zie-framework/.config` exists → if not, recommend `/init`.

## Steps

1. Print: `[Exploring codebase...]`

2. Invoke `Agent(subagent_type=Explore)`:
   - **Before scanning code**: read existing project docs as primary
     sources — prefer documented intent over inferred code structure:
     `README.md`, `CHANGELOG.md`, `ARCHITECTURE.md`, `AGENTS.md`,
     `docs/**`, any `**/specs/*.md`, `**/plans/*.md`,
     `**/decisions/*.md` outside `zie-framework/`
   - Same task and exclusion list as `/init` existing project scan:
     scan every file, return structured analysis covering architecture,
     components, tech stack, data flow, decisions, test strategy, active
     areas.
   - Exclude: `node_modules/`, `.git/`, `build/`, `dist/`, `.next/`,
     `__pycache__/`, `coverage/`, `zie-framework/`
     (`*.pyc` is covered by `__pycache__/` exclusion)

   Print: "✓ Explored. Building knowledge drafts..."

3. Read Agent report and draft updated versions of all four knowledge files:
   - `zie-framework/PROJECT.md`
   - `zie-framework/project/architecture.md`
   - `zie-framework/project/components.md`
   - `zie-framework/project/context.md`

4. Present all four drafts inline as markdown code blocks. Ask:
   "Does this look accurate? Reply 'yes' to write, or describe corrections."

5. If corrections → apply → re-present → repeat until user replies 'yes'
   or 'y' (case-insensitive). No iteration limit.

6. Overwrite all four knowledge files on disk.

7. **Detect migratable documentation** — scan project root
   (excluding `zie-framework/`, `node_modules/`, `.git/`) for
   files matching these patterns:

   | Pattern | Destination |
   | --- | --- |
   | `**/specs/*.md`, `**/spec/*.md` | `zie-framework/specs/` |
   | `**/plans/*.md`, `**/plan/*.md` | `zie-framework/plans/` |
   | `**/decisions/*.md`, `**/adr/*.md` | `zie-framework/decisions/` |
   | `ADR-*.md` (at project root) | `zie-framework/decisions/` |

   Skip always: `README.md`, `CHANGELOG.md`, `LICENSE*`,
   `CLAUDE.md`, `AGENTS.md`, files already inside `zie-framework/`,
   `plans/archive/` (archived historical plans),
   and any `docs/` tree that contains `index.md` or `_sidebar.md`
   at its root (public doc site).

   If candidates found, print:

   ```text
   Found documentation that can be migrated into zie-framework/:

     docs/specs/foo.md  →  zie-framework/specs/foo.md
     docs/plans/bar.md  →  zie-framework/plans/bar.md

   Migrate these files? (yes / no / select)
   ```

   - `yes` → migrate all using `git mv`
   - `no` → skip silently
   - `select` → confirm each file individually (y/n per file)

   After migration, print the list of moved files.
   If no candidates found, skip silently.

8. Recompute `knowledge_hash` using the same algorithm as `/init`.
   Run inline Python:

   ```bash
   python3 hooks/knowledge-hash.py
   ```

9. Merge into `zie-framework/.config` (never remove existing fields):

   ```json
   {
     "knowledge_hash": "<new hash>",
     "knowledge_synced_at": "<YYYY-MM-DD>"
   }
   ```

10. Print:

   ```text
   Knowledge docs updated.

   knowledge_hash : <first 8 chars of hash>...
   synced_at      : <YYYY-MM-DD>

   Run /status to verify sync status.
   ```

## ขั้นตอนถัดไป

→ `/status` — ยืนยันว่า Knowledge แสดง ✓ synced

## Notes

- Idempotent — safe to run multiple times
- All doc updates require user 'yes' — never auto-overwrites
- Does not change ROADMAP, Makefile, VERSION, or CLAUDE.md
