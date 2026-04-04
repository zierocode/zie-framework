---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-silent-config-parse-failures.md
---

# Warn on Silent Config Parse Failures — Design Spec

**Problem:** `auto-test.py` (line 73) and `session-resume.py` (line 28) silently swallow JSON parse exceptions on `.config` load and continue with an empty `config` dict, giving the user no indication that their config file is corrupted and the hook is running with wrong defaults.

**Approach:** In both hooks, replace the bare `except Exception: pass` in the config-load block with `except Exception as e: print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)`. No other behavior changes — the hook still continues with defaults. The warning goes to stderr so it appears in Claude's hook output without blocking execution.

**Components:**
- `hooks/auto-test.py` — lines 71-74: add `as e` and `print(...)` to except clause
- `hooks/session-resume.py` — lines 25-29: add `as e` and `print(...)` to except clause

**Data Flow:**
1. Hook reads `zf / ".config"` file (existing)
2. `json.loads()` raises `json.JSONDecodeError` or other exception (corrupt file scenario)
3. **NEW:** stderr warning printed with exception message and `[zie]` prefix
4. `config` remains `{}` and hook proceeds with defaults (unchanged)

**Edge Cases:**
- `.config` file does not exist — guarded by `if config_file.exists()` before the try block in both hooks; warning never fires for missing file
- `.config` is valid JSON but missing expected keys — not a parse error; `config.get(key, default)` handles this silently as intended
- Warning fires on every hook invocation for a corrupt file — acceptable; repeated stderr output is the correct signal to fix the file
- `config_file.read_text()` raises `OSError` (permissions) — caught by same except clause, produces the same warning

**Out of Scope:**
- Validating config schema beyond JSON parse
- Auto-repairing or resetting a corrupt `.config` file
- Centralizing config loading into `utils.py` (separate refactor)
