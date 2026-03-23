---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-knowledge-hash-dedup.md
---

# Knowledge Hash Deduplication — Design Spec

**Problem:** The `knowledge_hash` Python inline is copy-pasted identically
into `commands/zie-init.md`, `commands/zie-status.md`, and
`commands/zie-resync.md`; a change to the algorithm requires editing all three
command files in sync.

**Approach:** Extract the inline Python block into a standalone script
`hooks/knowledge-hash.py`. All three commands replace their inline `python3
-c "..."` block with a `python3 hooks/knowledge-hash.py` call. The script
accepts an optional `--root` argument defaulting to `.`.

**Components:**

- `hooks/knowledge-hash.py` — new standalone script (single source of truth)
- `commands/zie-init.md` — replace inline Python block in step 2f
- `commands/zie-status.md` — replace inline Python block in step 4
- `commands/zie-resync.md` — replace inline Python block in step 8

**Data Flow:**

1. Create `hooks/knowledge-hash.py`:

   ```python
   #!/usr/bin/env python3
   """Compute knowledge_hash for a zie-framework project.

   Prints the SHA-256 hex digest to stdout.
   Usage: python3 hooks/knowledge-hash.py [--root <path>]
   """
   import argparse
   import hashlib
   from pathlib import Path

   EXCLUDE = {
       'node_modules', '.git', 'build', 'dist', '.next',
       '__pycache__', 'coverage', 'zie-framework'
   }
   CONFIG_FILES = [
       'package.json', 'requirements.txt', 'pyproject.toml',
       'Cargo.toml', 'go.mod'
   ]

   parser = argparse.ArgumentParser()
   parser.add_argument('--root', default='.')
   args = parser.parse_args()

   root = Path(args.root)
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
   ```

2. In each command file, replace the full `python3 -c "..."` heredoc with:

   ```bash
   python3 hooks/knowledge-hash.py
   ```

   The output (hex digest printed to stdout) is captured and used identically
   as before.

3. Add `hooks/knowledge-hash.py` to the `lint` target in `Makefile`:

   ```makefile
   lint:
       python3 -m py_compile hooks/*.py && echo "All hooks compile OK"
   ```

   (This already globs `hooks/*.py` so no change needed.)

4. Add a `tests/test_knowledge_hash.py` with at least one test: run the
   script against a temp directory tree and confirm the output is a 64-char
   hex string.

**Edge Cases:**

- Commands run from the project root where `hooks/` exists — if a command is
  run from a different directory, `hooks/knowledge-hash.py` path must be
  relative to the project root. Commands already assume project root CWD;
  acceptable.
- `--root` flag allows testing and future use from CI scripts
- The algorithm must remain byte-for-byte identical to the current inline
  versions — no logic changes, only extraction

**Out of Scope:**

- Making `knowledge-hash.py` a hook event handler (it is a utility script,
  not a hook)
- Caching the hash computation result
