---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safety-check-regex-bypass.md
---

# Safety-Check Regex Bypass — Design Spec

**Problem:** `safety-check.py` block patterns can be evaded by inserting extra whitespace (e.g. `rm  -rf  ./`, `git push -u  origin  main`) because `cmd` retains multi-space sequences before regex matching.

**Approach:** Normalize whitespace on `cmd` before pattern matching — replace all runs of whitespace with a single space using `re.sub(r'\s+', ' ', cmd.strip().lower())`. Update the three `rm -rf` patterns and the two push-to-main patterns to use `\s+` instead of `\s+` where they currently use literal spaces, ensuring the fix is consistent even if normalization is skipped. No new dependency required.

**Components:**
- `hooks/safety-check.py` — `cmd` assignment + `BLOCKS` pattern list
- `tests/test_safety_check.py` — new bypass-variant test cases

**Data Flow:**
1. Hook reads `command` string from stdin JSON event.
2. `cmd = re.sub(r'\s+', ' ', command.strip().lower())` collapses all whitespace.
3. Normalized `cmd` is passed through `BLOCKS` patterns unchanged.
4. `rm  -rf  ./` becomes `rm -rf ./` before matching — pattern fires correctly.
5. `git push -u  origin  main` becomes `git push -u origin main` — push-to-main pattern fires.
6. `sys.exit(2)` blocks the command as before.

**Edge Cases:**
- Commands with embedded newlines (multi-line Bash strings) — normalization converts `\n` to space, preserving block coverage.
- Patterns using `\s+` internally still work correctly against the normalized single-space string.
- `WARNS` patterns receive the same normalized `cmd`, so no separate treatment needed.

**Out of Scope:**
- Unicode lookalike characters (e.g. non-breaking space) — separate hardening item.
- Adding new block patterns beyond existing scope.
- Changing the `sys.exit(2)` protocol.
