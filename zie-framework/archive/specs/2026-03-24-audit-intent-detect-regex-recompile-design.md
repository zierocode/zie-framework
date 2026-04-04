---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-intent-detect-regex-recompile.md
---

# Intent-Detect Module-Level Regex Compilation — Design Spec

**Problem:** `intent-detect.py` builds `COMPILED_PATTERNS` inside the script body (lines 80-83) rather than at module level, so Python's `.pyc` cache cannot persist compiled regex objects between invocations — every `UserPromptSubmit` event pays full compilation cost for all 96 patterns.

**Approach:** Move both `PATTERNS` and `COMPILED_PATTERNS` to module-level constants (outside any `if __name__ == "__main__"` guard). Python compiles module-level code once and caches it in `__pycache__/<file>.cpython-3x.pyc`. Subsequent invocations load the `.pyc` bytecode and the dict literal is reconstructed cheaply — regex objects themselves are not persisted across processes, but the bytecode cache eliminates re-parsing the pattern strings and saves `re.compile()` overhead. No logic changes; only code placement changes.

**Components:**
- `hooks/intent-detect.py` — move `PATTERNS` dict and `COMPILED_PATTERNS` dict-comprehension from lines 33-83 to module top-level (after imports, before any conditional logic)

**Data Flow:**
1. Python interpreter loads `intent-detect.py`
2. `.pyc` cache hit: bytecode loads; `PATTERNS` and `COMPILED_PATTERNS` are reconstructed from bytecode constants at module load time
3. Script body runs: reads event, applies `message` guards, then scores against already-constructed `COMPILED_PATTERNS`
4. Output printed; script exits

**Edge Cases:**
- `intent-detect.py` is run with `-B` flag (no `.pyc` writes) — compilation still happens once per process; no regression, just no caching benefit
- `__pycache__` directory not writable (read-only deploy) — Python falls back to in-memory compile; behavior unchanged
- Pattern list is modified in future — `COMPILED_PATTERNS` at module level is rebuilt automatically on next `.pyc` invalidation (mtime change on source file)
- Hook is not wrapped in `if __name__ == "__main__"` guard currently — this is already the case; moving constants to module level is consistent with existing structure

**Out of Scope:**
- Persisting compiled regex objects to disk across process boundaries
- Reducing the number of patterns or consolidating categories
- Benchmarking the actual latency improvement
