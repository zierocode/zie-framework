---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-cwd-init-boilerplate.md
---

# CLAUDE_CWD Initialization Boilerplate Deduplication — Design Spec

**Problem:** `Path(os.environ.get("CLAUDE_CWD", os.getcwd()))` is copied
identically into 6 hooks; changing the env var name or fallback logic requires
editing all 6 files.

**Approach:** Add a `get_cwd()` helper to `hooks/utils.py`. Each of the 6
hooks replaces its inline expression with `cwd = get_cwd()`.

**Components:**

- `hooks/utils.py` — add `get_cwd()` function
- `hooks/auto-test.py` — replace inline expression
- `hooks/intent-detect.py` — replace inline expression
- `hooks/session-cleanup.py` — replace inline expression
- `hooks/session-learn.py` — replace inline expression
- `hooks/session-resume.py` — replace inline expression
- `hooks/wip-checkpoint.py` — replace inline expression

**Data Flow:**

1. Add to `hooks/utils.py`:

   ```python
   def get_cwd() -> Path:
       """Return the working directory for the current Claude Code session.

       Prefers CLAUDE_CWD env var (set by Claude Code) over os.getcwd().
       """
       return Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
   ```

   Add `import os` to `utils.py` imports (currently absent).

2. In each hook, replace:

   ```python
   cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
   ```

   with:

   ```python
   cwd = get_cwd()
   ```

   Add `get_cwd` to the existing `from utils import ...` line in each hook.

3. Run `make test-unit` — behaviour is identical so all tests must pass.

**Edge Cases:**

- `safety-check.py` does not use `CLAUDE_CWD` at all (it only checks tool
  input paths) — no change needed there
- `utils.py` is imported by hooks at runtime with `sys.path.insert(0,
  os.path.dirname(__file__))` — adding `import os` to `utils.py` is safe
  because `os` is stdlib
- If `CLAUDE_CWD` is set to an empty string, `Path("")` resolves to `Path(".")`
  which is equivalent to `os.getcwd()` — acceptable behaviour

**Out of Scope:**

- Validating that `CLAUDE_CWD` points to an existing directory (hooks already
  check `zf.exists()` downstream)
- Centralising the `zf = cwd / "zie-framework"` pattern (separate, lower-value
  dedup)
