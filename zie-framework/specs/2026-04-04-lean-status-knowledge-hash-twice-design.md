# Lean Status: Deduplicate knowledge-hash computation — Design Spec

**Problem:** `/status` runs `python3 hooks/knowledge-hash.py` twice per invocation — once via bang-injection at command load time (line 21) and once again as an explicit Bash call in Step 4. The script does a full `rglob("*")` across the project both times, producing identical output. This is pure waste: ~100 extra tokens of context and double the filesystem I/O on every `/status` call.

**Approach:** Capture the bang-injected hash output in a named binding (`knowledge_hash_current`) at the top of the command, then reference that binding in Step 4 for the drift comparison instead of spawning a second subprocess. No behavioral change — same hash value, same comparison logic, same output format. The bang injection already executes first, its stdout is already available in-context; Step 4 just needs to read it rather than recompute it.

**Components:**
- `commands/status.md` — primary change: restructure bang injection + Step 4
- `tests/unit/test_zie_status_drift.py` — existing test file; extend with a new assertion that `knowledge-hash.py` appears only once as an explicit Bash call (or zero times if we count bang injections separately)

**Data Flow:**
1. Command loads → bang injection fires: `!python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"` → result stored in-context as `knowledge_hash_current`
2. Step 4 reads `knowledge_hash_current` from in-context binding — no Bash call
3. Step 4 reads `knowledge_hash` from `zie-framework/.config`
4. Step 4 compares `knowledge_hash_current` vs stored hash → prints status row
5. No second subprocess spawned

**Edge Cases:**
- `knowledge-hash.py` unavailable → bang injection already outputs `"knowledge-hash: unavailable"`; Step 4 checks for this sentinel string and falls back to `? no baseline — run /resync` (same as current missing-hash path)
- `.config` missing `knowledge_hash` key → Step 4 outputs `? no baseline — run /resync` unchanged
- Hash script exits non-zero (permission error, etc.) → bang injection's `|| echo` guard provides the sentinel; Step 4 handles it gracefully

**Out of Scope:**
- Changes to `knowledge-hash.py` itself — script is not modified
- Changes to `/resync` or `/init` commands — they manage their own hash computation
- Caching the hash result to disk — the mtime-gate cache in `--check` mode is a different concern
- Performance optimization of `knowledge-hash.py` internals (rglob algorithm, EXCLUDE list)

---

## Acceptance Criteria

- [ ] `commands/status.md` references `python3 hooks/knowledge-hash.py` (non-bang) **zero times** in Step 4 — the bang injection at the top is the only execution
- [ ] The Knowledge drift comparison in Step 4 reads the already-injected hash value, not a fresh subprocess
- [ ] `/status` output is identical to before (same Knowledge row format, same sentinel handling)
- [ ] `test_zie_status_drift.py` has a passing test asserting that `knowledge-hash.py` explicit Bash call count in `status.md` Step 4 is zero
