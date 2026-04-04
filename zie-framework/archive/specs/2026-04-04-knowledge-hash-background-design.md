# Spec: Move knowledge-hash Drift Check Off SessionStart Critical Path
status: draft

## Problem

`session-resume.py` (lines 142–155) runs `subprocess.run([sys.executable, knowledge-hash.py, "--check", ...], timeout=10)` **synchronously** on the SessionStart critical path. This adds up to 10 seconds of wall-clock latency to every Claude session start, proportional to codebase size. The drift warning is purely informational — Claude does not need it before becoming interactive.

Current code:
```python
_result = _sp.run(
    [sys.executable, _kh_script, "--check", "--root", str(cwd)],
    capture_output=True, text=True, timeout=10,
)
if _result.stdout.strip():
    print(_result.stdout.strip())
```

## Solution

Replace `subprocess.run` with `subprocess.Popen` (fire-and-forget) so the drift check runs in the background and never blocks SessionStart.

- Use `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL` — output is discarded since we cannot wait for it synchronously.
- The drift warning will no longer appear in session context. This is acceptable: the check is informational only and `/zie-status` or `/zie-resync` can surface drift on demand.
- No changes to `hooks.json` required.
- No new hook registration needed.

**Chosen option: subprocess.Popen (fire-and-forget)**

Rationale: simplest change, no hooks.json churn, no new hook file, consistent with the codebase's established pattern of discarding background results (e.g., `wip-checkpoint.py`, `session-cleanup.py`).

```python
import subprocess as _sp
_kh_script = os.environ.get(
    "ZIE_KNOWLEDGE_HASH_SCRIPT",
    os.path.join(os.path.dirname(__file__), "knowledge-hash.py"),
)
_sp.Popen(
    [sys.executable, _kh_script, "--check", "--root", str(cwd)],
    stdout=_sp.DEVNULL,
    stderr=_sp.DEVNULL,
)
```

## Acceptance Criteria

1. `session-resume.py` drift check block uses `subprocess.Popen` with `stdout=DEVNULL, stderr=DEVNULL` — no `subprocess.run` call for the drift check.
2. SessionStart no longer blocks on the drift check subprocess.
3. Hook exits 0 and does not crash if `Popen` fails (e.g., script missing) — existing `except Exception` guard handles it.
4. Existing `TestSessionResumeDriftDetection` tests that assert on drift output (`test_prints_drift_warning_when_hash_mismatch`, `test_silent_when_hash_matches`, `test_output_line_count_unchanged_without_drift`) are updated to reflect that drift output is no longer printed inline — those assertions are removed or replaced.
5. `test_exits_zero_when_knowledge_hash_crashes` still passes (Popen with bad path raises `FileNotFoundError` caught by the inner `except Exception`).
6. Output line count tests (4 lines) remain green — no drift line is appended.
7. All other `TestSessionResume*` tests continue to pass.
8. `make test-fast` green on the changed file.

## Out of Scope

- Surfacing the drift warning via a separate hook registration.
- Deferring to `UserPromptSubmit`.
- Changing `knowledge-hash.py` itself.
- Adding a new config key to toggle background vs. synchronous mode.
