---
slug: audit-hook-outer-guard
status: approved
approved: true
date: 2026-04-01
---
# Plan: Add Outer Try/Except Guard to session-resume, session-learn, wip-checkpoint

## Tasks

- [ ] **Task 1 — Wrap `session-resume.py` in outer guard**
  - Move all logic from `event = read_event()` through the final drift-detection
    `except` block inside a top-level `try: ... except Exception: sys.exit(0)`.
  - The two existing inner `except Exception as e: print(...)` handlers (env-file
    write and drift check) remain unchanged.
  - Result: any exception from `read_event()`, `load_config()`,
    `parse_roadmap_now()`, or `version_file.read_text()` exits 0 silently.

- [ ] **Task 2 — Wrap `session-learn.py` in outer guard**
  - Move all logic from `event = read_event()` through the final
    `call_zie_memory_api` try/except block inside a top-level
    `try: ... except Exception: sys.exit(0)`.
  - The existing `except Exception as e: print(...)` around `call_zie_memory_api`
    remains as the inner tier.
  - Result: `OSError` from `atomic_write()` or any other unguarded call exits 0.

- [ ] **Task 3 — Wrap `wip-checkpoint.py` in outer guard**
  - Move all logic from `event = read_event()` through the final
    `call_zie_memory_api` try/except block inside a top-level
    `try: ... except Exception: sys.exit(0)`.
  - The existing `except Exception as e: print(...)` blocks around counter reads
    and the API call remain as the inner tier.
  - Result: an exception from `read_event()` or `get_cwd()` exits 0.

- [ ] **Task 4 — Unit test: outer guard for `session-resume.py`**
  - Add `TestSessionResumeOuterGuard` class to
    `tests/unit/test_hooks_session_resume.py` with two test methods:
    - `test_empty_stdin_exits_zero` — `input=""` → `returncode == 0`, no `Traceback` in stderr
    - `test_invalid_json_exits_zero` — `input="not json"` → `returncode == 0`, no `Traceback` in stderr
  - **RED**: Run `pytest tests/unit/test_hooks_session_resume.py::TestSessionResumeOuterGuard -x` — must FAIL (hook raises unguarded exception)
  - Implement Task 1 (outer guard wrap)
  - **GREEN**: Run `pytest tests/unit/test_hooks_session_resume.py::TestSessionResumeOuterGuard -x` — must PASS

- [ ] **Task 5 — Unit test: outer guard for `session-learn.py`**
  - Add `TestSessionLearnOuterGuard` class to
    `tests/unit/test_hooks_session_learn.py` with two test methods:
    - `test_empty_stdin_exits_zero` — `input=""` → `returncode == 0`, no `Traceback` in stderr
    - `test_invalid_json_exits_zero` — `input="not json"` → `returncode == 0`, no `Traceback` in stderr
  - **RED**: Run `pytest tests/unit/test_hooks_session_learn.py::TestSessionLearnOuterGuard -x` — must FAIL
  - Implement Task 2 (outer guard wrap)
  - **GREEN**: Run `pytest tests/unit/test_hooks_session_learn.py::TestSessionLearnOuterGuard -x` — must PASS

- [ ] **Task 6 — Unit test: outer guard for `wip-checkpoint.py`**
  - Add `TestWipCheckpointOuterGuard` class to
    `tests/unit/test_hooks_wip_checkpoint.py` with one test method:
    - `test_empty_stdin_exits_zero` — `input=""` → `returncode == 0`, no `Traceback` in stderr, stdout empty
  - Note: `test_invalid_json_exits_zero` already exists in `TestWipCheckpointGuardrails` — new class targets the specific `read_event()` EOF path
  - **RED**: Run `pytest tests/unit/test_hooks_wip_checkpoint.py::TestWipCheckpointOuterGuard -x` — must FAIL
  - Implement Task 3 (outer guard wrap)
  - **GREEN**: Run `pytest tests/unit/test_hooks_wip_checkpoint.py::TestWipCheckpointOuterGuard -x` — must PASS

- [ ] **Task 7 — Run `make test-ci` and confirm no regressions**

## Test Strategy

**Unit tests only** — all three hooks are tested via subprocess (`subprocess.run`)
matching the existing hook test pattern in this repo. No integration tests needed.

Key scenarios per hook:

| Hook | Trigger | Expected |
|---|---|---|
| `session-resume.py` | `input=""` (EOF → JSONDecodeError in read_event) | exit 0, no Traceback |
| `session-resume.py` | `input="not json"` | exit 0, no Traceback |
| `session-learn.py` | `input=""` | exit 0, no Traceback |
| `session-learn.py` | `input="not json"` | exit 0, no Traceback |
| `wip-checkpoint.py` | `input=""` | exit 0, no Traceback |

All test classes follow the `subprocess.run([sys.executable, HOOK], input=...,
capture_output=True, text=True)` pattern established in the existing test files.

Inner-tier handlers are not changed — existing tests that assert `[zie-framework]`
stderr prefixes continue to pass unchanged (AC4 / AC6).

## Rollout

1. Implement Tasks 1–3 (hook edits) — no behaviour change, pure wrapping.
2. Implement Tasks 4–6 (unit tests) — RED first, confirm they fail on current code,
   then GREEN after wrapping is applied.
3. Run `make test-ci` (Task 7) — gate on full suite passing.
4. No config changes. No dependency changes. No migration steps needed.
