---
date: 2026-04-15
status: approved
slug: audit-error-handling-cleanup
---

# Implementation Plan: audit-error-handling-cleanup

## Steps

1. **Create `hooks/utils_error.py`** — single helper `log_error(hook, op, exc)` that writes `[zie-framework] {hook}: {op} failed — {exc}` to stderr. Keeps logging format consistent across all hooks.

2. **Phase 1: Add stderr logging** — Walk all 144 `except Exception` blocks. For bare `except Exception: pass` or `except Exception:` with no body, add `log_error(hook_name, operation, e)`. For `except Exception as e:` blocks that silently swallow, add the same log call before `pass`/`sys.exit(0)`. Process files by priority: stop-handler, session-resume, utils_roadmap, intent-sdlc, post-tool-use, then remainder.

3. **Phase 2: Narrow exception types** — For each `except Exception as e:` block where the try-body only does file reads, JSON parsing, or subprocess calls, replace with specific catches (`FileNotFoundError`, `json.JSONDecodeError`, `OSError`, `subprocess.TimeoutExpired`). Keep a broad fallback `except Exception` with `log_error` for anything unexpected. Only change blocks where the mapping is clear — leave ambiguous ones as broad catch + log.

4. **Lint check** — Run `make lint` after each file to catch syntax errors early.

5. **Run full test suite** — `make test-fast` to confirm no regressions.

## Tests

- **Test `log_error` output** — Unit test that `log_error("stop-handler", "git_status", Exception("fail"))` writes the expected format to stderr.
- **Test specific catch narrow** — For each narrowed block, test that the specific exception is caught and logged, and that unexpected exceptions still hit the broad fallback.
- **Test no behavior change** — Existing tests pass unchanged; hooks still exit 0 per ADR-003.

## Acceptance Criteria

- [ ] Every `except Exception` block writes context to stderr (no silent swallowing)
- [ ] At least 40% of broad catches narrowed to specific exception types (up from 10% → 50%+)
- [ ] `make test-fast` passes with zero failures
- [ ] `make lint` passes
- [ ] No change to hook exit codes (all remain exit 0 per ADR-003)