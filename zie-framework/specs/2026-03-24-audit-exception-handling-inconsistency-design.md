---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-exception-handling-inconsistency.md
---

# Standardize Hook Exception Handling Convention — Design Spec

**Problem:** Hooks use at least three different error patterns — silent exit, noisy stderr print, and mixed approaches within the same file — with no documented rule, making hook debugging unpredictable.

**Approach:** Establish and document a two-tier convention: (1) the **outer guard** (event parse + early-exit checks) catches silently and calls `sys.exit(0)` — this tier must never block Claude; (2) **inner operations** (file I/O, API calls, subprocess) catch with `except Exception as e` and print a `[zie-framework] <hook-name>: <e>` warning to stderr. Apply this convention consistently across all hooks and document it in `CLAUDE.md` under a new "Hook Error Handling" section.

**Components:**
- `hooks/auto-test.py` — line 49: outer guard is correct (silent); line 130 inner catch is correct; no change needed
- `hooks/session-learn.py` — line 15: outer guard correct; line 64 inner correct; consistent already
- `hooks/wip-checkpoint.py` — line 14: outer guard correct; line 41 and 81 inner correct; consistent already
- `hooks/session-cleanup.py` — outer guard (line 11) correct; inner catch (line 21) correct; consistent already
- `hooks/intent-detect.py` — line 11: outer guard correct; no inner operations needing catch; consistent already
- `hooks/session-resume.py` — outer guard correct; config-load except (line 28) is bare `pass` — change to log (covered by audit-silent-config-parse-failures)
- `CLAUDE.md` — add "Hook Error Handling Convention" section under Key Rules

**Data Flow:**
1. Hook receives event on stdin
2. **Outer guard** — `json.loads()` in try/except Exception → `sys.exit(0)` on failure (silent, never blocks)
3. Early-exit checks (missing env, uninitialized project) — silent `sys.exit(0)`
4. **Inner operations** — each discrete operation (file read/write, API call, subprocess) wrapped in try/except that logs to stderr with `[zie-framework] <hook>: <e>`
5. Hook exits normally; Claude never sees an exception

**Edge Cases:**
- An inner operation is critical enough that failure should abort the hook — still exit 0 after logging; Claude must not be blocked
- Multiple inner operations in sequence — each gets its own try/except so one failure does not suppress subsequent operation errors
- Third-party exceptions with non-str `__str__` — `f"... {e}"` always produces a string; safe

**Out of Scope:**
- Structured logging or log levels beyond stderr print
- Centralizing exception handling into a decorator or context manager
- Changing exit codes (all hooks exit 0)
