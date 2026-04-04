# Plan: Move knowledge-hash Drift Check Off SessionStart Critical Path
status: approved

## Tasks

- [ ] RED: Update `TestSessionResumeDriftDetection` — remove assertions that expect drift output in stdout (`test_prints_drift_warning_when_hash_mismatch` asserts `"Knowledge drift detected" in r.stdout`, `test_silent_when_hash_matches` asserts `"drift" not in r.stdout.lower()`). Replace with assertions that: (a) hook exits 0, (b) stdout contains exactly 4 lines (no drift line appended). `test_output_line_count_unchanged_without_drift` stays as-is. `test_exits_zero_when_knowledge_hash_crashes` stays as-is. Run `make test-fast` — expect RED on the two changed assertions (they will now fail because drift output no longer appears once we apply the fix; but first confirm they are currently GREEN before changing the hook, meaning the test change itself needs to invert the expectation).

  Concrete test changes in `tests/unit/test_hooks_session_resume.py`:
  - `test_prints_drift_warning_when_hash_mismatch`: change assertion to `assert r.returncode == 0` and `assert len(r.stdout.strip().splitlines()) == 4` (no drift line, Popen fires-and-forgets).
  - `test_silent_when_hash_matches`: remove `assert "drift" not in r.stdout.lower()` (already passes, but simplify to just `assert r.returncode == 0`).

- [ ] GREEN: In `hooks/session-resume.py` replace the synchronous drift check block (lines 141–155) with a `subprocess.Popen` fire-and-forget call:

  ```python
  # Drift detection — fire-and-forget background check
  try:
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
  except Exception as e:
      print(f"[zie-framework] session-resume: drift check failed: {e}", file=sys.stderr)
  ```

  Run `make test-fast` — expect GREEN.

- [ ] REFACTOR: Run `make lint` — fix any ruff violations. Confirm no stray `capture_output`, `text=True`, or `timeout=` in the drift check block. Run `make test-ci` for full green.

## Files to Change

| File | Change |
| --- | --- |
| `hooks/session-resume.py` | Replace `subprocess.run` drift check (lines 141–155) with `subprocess.Popen` fire-and-forget |
| `tests/unit/test_hooks_session_resume.py` | Update `TestSessionResumeDriftDetection` — remove inline drift output assertions; assert exit 0 + 4-line output count instead |
