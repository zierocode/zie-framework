---
approved: true
approved_at: 2026-04-04
backlog: backlog/sec-shell-injection-confirm-wrap.md
---

# sec-shell-injection-confirm-wrap — Design Spec

**Problem:** `_is_safe_for_confirmation_wrapper()` in `hooks/safety-check.py` does not reject shell metacharacters `>`, `<`, `|`, and `\n`. Commands containing these characters pass the guard and are interpolated unquoted into the confirm-wrap compound statement `&& { {command}; }`, enabling stdout/stdin redirect and pipe injection.

**Approach:** Extend the `_DANGEROUS_COMPOUND_RE` regex in `hooks/safety-check.py` to include `>`, `<`, `|`, and `\n`. This is a one-character-class addition to the existing guard — no behavior change to the confirm-wrap rewrite path itself, no new code paths, and no risk to hook safety. A matching set of pytest unit tests covers the four new rejected characters and confirms previously-accepted safe commands still pass.

**Components:**
- `hooks/safety-check.py` — extend `_DANGEROUS_COMPOUND_RE` pattern (line 32)
- `tests/unit/test_safety_check_confirm_wrap.py` — new test file covering the guard function and the full confirm-wrap path for injected `>`, `<`, `|`, `\n`

**Data Flow:**
1. Claude issues a Bash tool call with a command matching a `CONFIRM_PATTERNS` entry (e.g. `rm -rf ./foo > /etc/passwd`).
2. `safety-check.py` Bash branch calls `_is_safe_for_confirmation_wrapper(command)`.
3. The function runs `_DANGEROUS_COMPOUND_RE.search(command)`.
4. With the fix, `>` is matched → function returns `False` → hook logs a stderr warning and exits 0 (no confirm-wrap applied, command passes through unmodified for Claude to execute normally).
5. Without the fix (current bug), `>` is not matched → function returns `True` → command is interpolated unquoted into the rewritten shell string → redirect injection is possible.

**Edge Cases:**
- `>` in a here-doc or quoted argument (e.g. `echo "foo > bar"`) — the guard operates on the raw command string; this may produce a false positive (skip the confirm-wrap). Acceptable: the confirm-wrap is a UX feature, not a security gate. False positives are safe.
- `\n` (literal newline in the command string) — must be matched as the character `\n`, not the escape sequence. The regex character class `[\n]` matches the actual newline byte.
- Bandit B602/B603 — `subprocess=True` is not used here; the confirm-wrap uses `updatedInput` output. Bandit scan should show zero new findings after this change.
- Existing tests — no existing tests target `_is_safe_for_confirmation_wrapper` directly; new tests are purely additive.

**Out of Scope:**
- Replacing the confirm-wrap mechanism with `shlex.quote` wrapping (a larger refactor with different UX implications)
- Adding `>` / `<` / `|` to the hard-block `BLOCKS` list in `utils_safety.py`
- Modifying `CONFIRM_PATTERNS` entries
- Running Bandit in CI (tracked separately in backlog)
