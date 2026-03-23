---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-knowledge-hash-dedup.md
spec: specs/2026-03-24-audit-knowledge-hash-dedup-design.md
---

# Knowledge Hash Deduplication — Implementation Plan

**Goal:** Extract the inline `knowledge_hash` Python block from three command files into a standalone `hooks/knowledge-hash.py` script that all three commands invoke via `python3 hooks/knowledge-hash.py`.
**Architecture:** `hooks/knowledge-hash.py` is a new standalone utility script (not a hook event handler). It accepts an optional `--root` argument. All three command files replace their `python3 -c "..."` heredoc with a single `python3 hooks/knowledge-hash.py` call. A `tests/unit/test_knowledge_hash.py` file validates the script produces a 64-char hex digest. The algorithm is extracted verbatim — no logic changes.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/knowledge-hash.py` | Standalone script: compute and print SHA-256 knowledge hash |
| Modify | `commands/zie-init.md` | Replace inline python3 -c block in step 2f with script call |
| Modify | `commands/zie-status.md` | Replace inline python3 -c block in step 4 with script call |
| Modify | `commands/zie-resync.md` | Replace inline python3 -c block in step 8 with script call |
| Create | `tests/unit/test_knowledge_hash.py` | Test script produces valid 64-char hex digest |

## Task 1: Create hooks/knowledge-hash.py

**Acceptance Criteria:**
- `hooks/knowledge-hash.py` exists and is executable (chmod +x or called via `python3`)
- Running `python3 hooks/knowledge-hash.py` against any directory prints a 64-character lowercase hex string to stdout
- Running `python3 hooks/knowledge-hash.py --root /some/path` uses the given root
- The algorithm is byte-for-byte equivalent to the inline versions in the three command files
- `make lint` passes (the script compiles via `python3 -m py_compile hooks/*.py`)

**Files:**
- Create: `hooks/knowledge-hash.py`
- Create: `tests/unit/test_knowledge_hash.py`

- [ ] **Step 1: Write failing tests (RED)**
  Create `tests/unit/test_knowledge_hash.py`:

  ```python
  """Tests for hooks/knowledge-hash.py"""
  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  SCRIPT = REPO_ROOT / "hooks" / "knowledge-hash.py"


  class TestKnowledgeHashScript:
      def test_script_exists(self):
          assert SCRIPT.exists(), f"knowledge-hash.py not found at {SCRIPT}"

      def test_output_is_64_char_hex(self, tmp_path):
          result = subprocess.run(
              [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
              capture_output=True, text=True
          )
          assert result.returncode == 0
          output = result.stdout.strip()
          assert len(output) == 64
          assert all(c in "0123456789abcdef" for c in output)

      def test_same_input_produces_same_hash(self, tmp_path):
          (tmp_path / "subdir").mkdir()
          r1 = subprocess.run(
              [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
              capture_output=True, text=True
          ).stdout.strip()
          r2 = subprocess.run(
              [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
              capture_output=True, text=True
          ).stdout.strip()
          assert r1 == r2

      def test_default_root_runs_without_error(self):
          result = subprocess.run(
              [sys.executable, str(SCRIPT)],
              capture_output=True, text=True,
              cwd=str(REPO_ROOT)
          )
          assert result.returncode == 0
          assert len(result.stdout.strip()) == 64
  ```

  Run: `make test-unit` — must FAIL (script does not exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Create `hooks/knowledge-hash.py`:

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

  Run: `make test-unit` — must PASS
  Run: `make lint` — must PASS (script compiles)

- [ ] **Step 3: Refactor**
  No cleanup needed — script matches spec exactly.
  Run: `make test-unit` — still PASS

## Task 2: Replace inline python3 -c blocks in command files

**Acceptance Criteria:**
- `commands/zie-init.md` step 2f inline Python block is replaced with `python3 hooks/knowledge-hash.py`
- `commands/zie-status.md` step 4 inline Python block is replaced with `python3 hooks/knowledge-hash.py`
- `commands/zie-resync.md` step 8 inline Python block is replaced with `python3 hooks/knowledge-hash.py`
- The captured output (hex digest) is used identically in each command's surrounding logic
- No other content in the three command files is changed

**Files:**
- Modify: `commands/zie-init.md`
- Modify: `commands/zie-status.md`
- Modify: `commands/zie-resync.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — command file (Markdown) changes. Verified manually by reading each file and confirming the inline `python3 -c` block is gone and `python3 hooks/knowledge-hash.py` is present.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In each command file, locate the `python3 -c "..."` block that computes the knowledge hash. Replace the full multi-line `python3 -c` heredoc with:

  ```bash
  python3 hooks/knowledge-hash.py
  ```

  The surrounding variable capture (e.g. `knowledge_hash=$(python3 hooks/knowledge-hash.py)`) remains unchanged.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Grep for `python3 -c` across `commands/` — confirm no knowledge hash inline blocks remain.
  Run: `make test-unit` — still PASS
