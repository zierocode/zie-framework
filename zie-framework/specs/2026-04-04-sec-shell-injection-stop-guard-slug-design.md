# sec-shell-injection-stop-guard-slug — Design Spec

**Problem:** `stop-guard.py` interpolates a ROADMAP-derived `slug` directly into a `shell=True` subprocess string, creating a shell injection vector if the ROADMAP is tampered (malicious PR, compromised workspace). The `# nosec B602` annotation acknowledges the risk but does not mitigate it.

**Approach:** Replace the `shell=True` piped command with two sequential Python-native subprocess calls: (1) `git log --all -p -- zie-framework/ROADMAP.md` with `shell=False`, capturing stdout; (2) filter lines in Python using `re` — no shell, no injection surface, no nosec annotation. This eliminates the root cause rather than patching around it.

**Components:**
- `hooks/stop-guard.py` — `_run_nudges()` function, Nudge 1 block (lines 62–85)
- `hooks/utils_roadmap.py` — no changes (slug extraction logic untouched)
- `tests/test_stop_guard.py` — new test cases for slug with shell metacharacters

**Data Flow:**
1. `_run_nudges()` extracts `slug` from ROADMAP Now-lane via regex (existing logic, unchanged)
2. For each slug, run `subprocess.run(["git", "log", "--all", "-p", "--", "zie-framework/ROADMAP.md"], shell=False, capture_output=True, text=True, timeout=subprocess_timeout, cwd=str(cwd))`
3. Filter `result.stdout` lines in Python: find lines matching `+- [ ] <slug>` (re.escape applied), then scan backward up to 5 lines for a `Date:` line
4. Parse date, compute days delta, emit nudge if > 2 days
5. Remove `# nosec B602` annotation (no longer needed)
6. Remove `import re as _re` inside the loop — hoist to top of try block

**Edge Cases:**
- Slug contains shell metacharacters (`$(cmd)`, backtick, `|`, `;`, `&`, `>`, `<`) — `re.escape(slug)` ensures safe regex; no shell involved
- Slug is empty string — `re.escape("")` matches nothing, loop body skips cleanly
- `git log` returns non-zero (no commits yet) — `result.returncode != 0` check, `continue` to next slug
- `git log` stdout is very large (repo with many commits) — bounded by `timeout=subprocess_timeout`; Python regex scan is linear
- ROADMAP has no Now-lane items — `now_items_raw` is empty, loop body never executes
- `git log` output contains no match for slug — date_match is None, nudge not emitted (correct)

**Out of Scope:**
- Refactoring other subprocess calls in stop-guard.py (git status already uses list form)
- Changing nudge logic or thresholds
- Adding new nudges
- Modifying utils_roadmap.py slug extraction
