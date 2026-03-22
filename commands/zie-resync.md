---
description: Rescan codebase and update knowledge docs + knowledge hash. Run when drift detected or after major structural changes.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Agent
---

# /zie-resync — Rescan Codebase + Update Knowledge Docs

Full rescan of project codebase. Updates PROJECT.md, project/architecture.md,
project/components.md, project/decisions.md, and knowledge_hash in .config.
All updates require user confirmation before writing.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Check `zie-framework/.config` exists → if not, recommend `/zie-init`.

## Steps

1. Print: "Rescanning codebase..."

2. Invoke `Agent(subagent_type=Explore)`:
   - Same task and exclusion list as `/zie-init` existing project scan:
     scan every file, return structured analysis covering architecture,
     components, tech stack, data flow, decisions, test strategy, active
     areas.
   - Exclude: `node_modules/`, `.git/`, `build/`, `dist/`, `.next/`,
     `__pycache__/`, `coverage/`, `zie-framework/`
     (`*.pyc` is covered by `__pycache__/` exclusion)

3. Read Agent report and draft updated versions of all four knowledge files:
   - `zie-framework/PROJECT.md`
   - `zie-framework/project/architecture.md`
   - `zie-framework/project/components.md`
   - `zie-framework/project/decisions.md`

4. Present all four drafts inline as markdown code blocks. Ask:
   "Does this look accurate? Reply 'yes' to write, or describe corrections."

5. If corrections → apply → re-present → repeat until user replies 'yes'
   or 'y' (case-insensitive). No iteration limit.

6. Overwrite all four knowledge files on disk.

7. Recompute `knowledge_hash` using the same algorithm as `/zie-init`.
   Run inline Python:

   ```bash
   python3 -c "
   import hashlib, os
   from pathlib import Path

   EXCLUDE = {
       'node_modules', '.git', 'build', 'dist', '.next',
       '__pycache__', 'coverage', 'zie-framework'
   }
   CONFIG_FILES = [
       'package.json', 'requirements.txt', 'pyproject.toml',
       'Cargo.toml', 'go.mod'
   ]

   root = Path('.')
   dirs = sorted(
       str(p.relative_to(root))
       for p in root.rglob('*')
       if p.is_dir()
       and not any(ex in p.parts for ex in EXCLUDE)
   )
   counts = sorted(
       f'{d}:{len(list((root / d).iterdir()))}'
       for d in dirs
   )
   configs = ''
   for cf in CONFIG_FILES:
       p = root / cf
       if p.exists():
           configs += p.read_text()

   s = '\n'.join(dirs) + '\n---\n'
   s += '\n'.join(counts) + '\n---\n'
   s += configs
   print(hashlib.sha256(s.encode()).hexdigest())
   "
   ```

8. Merge into `zie-framework/.config` (never remove existing fields):

   ```json
   {
     "knowledge_hash": "<new hash>",
     "knowledge_synced_at": "<YYYY-MM-DD>"
   }
   ```

9. Print:

   ```text
   Knowledge docs updated.

   knowledge_hash : <first 8 chars of hash>...
   synced_at      : <YYYY-MM-DD>

   Run /zie-status to verify sync status.
   ```

## ขั้นตอนถัดไป

→ `/zie-status` — ยืนยันว่า Knowledge แสดง ✓ synced

## Notes

- Idempotent — safe to run multiple times
- All doc updates require user 'yes' — never auto-overwrites
- Does not change ROADMAP, Makefile, VERSION, or CLAUDE.md
