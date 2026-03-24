---
approved: true
approved_at: 2026-03-24
backlog: backlog/fix-coverage-measurement.md
---

# Fix Coverage Measurement Infrastructure — Design Spec

**Problem:** All 80+ unit tests invoke hooks via `subprocess.run()`. pytest-cov cannot measure execution inside child processes launched this way, making 14 of 22 hooks appear at 0% coverage and the total appear as 20%. The measurement is meaningless: there is no way to identify genuinely untested paths or enforce a coverage gate.

**Approach:** Use `coverage.py`'s subprocess measurement feature via `COVERAGE_PROCESS_START`. When this env var is set and `coverage` is installed as a sitecustomize hook, child processes spawned by tests automatically participate in coverage collection. Concretely: (1) add a `.coveragerc` config file enabling `parallel=True` and `source=hooks`; (2) install the sitecustomize hook in the test environment via `coverage sitecustomize`; (3) update `make test-unit` to set `COVERAGE_PROCESS_START=.coveragerc` before pytest and run `coverage combine` + `coverage report` after. This approach requires zero changes to test code or hook source — existing subprocess-based tests start measuring automatically.

**Why not migrate tests to direct imports?** The hooks rely on `sys.exit()` as their primary communication channel, and most hook code runs at module level (not in importable functions). Migrating 80+ tests to import-based patterns requires refactoring every hook to expose testable functions — a much larger change than one config file. The subprocess measurement approach delivers the metric with minimal risk.

**Components:**
- `.coveragerc` (new file at project root) — coverage configuration
- `Makefile` — update `test-unit` target to set `COVERAGE_PROCESS_START` and run `coverage combine` + `coverage report`
- `pytest.ini` — no change needed (pytest-cov flags move to Makefile)
- `tests/` — no test code changes needed

**Data Flow:**
1. `make test-unit` runs: `coverage erase && COVERAGE_PROCESS_START=.coveragerc python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"` (no `--cov` flags — `coverage report` is the sole authority)
2. Each `subprocess.run(["python3", hook_path, ...], ...)` in test code spawns a child process
3. Python's sitecustomize imports `coverage` and starts measurement automatically when `COVERAGE_PROCESS_START` is set
4. Each child process writes a `.coverage.XXXXXXXX` parallel data file
5. After pytest completes: `coverage combine` merges all parallel `.coverage.*` files
6. `coverage report --show-missing --fail-under=50` prints the final report and exits non-zero if below threshold

**`.coveragerc` content:**
```ini
[run]
source = hooks
parallel = True
sigterm = True

[report]
show_missing = True
skip_covered = False

[paths]
hooks =
    hooks/
```

**Makefile `test-unit` target (updated):**
```makefile
test-unit: ## Fast unit tests with subprocess coverage measurement
    coverage erase
    COVERAGE_PROCESS_START=$(CURDIR)/.coveragerc \
        python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"
    coverage combine 2>/dev/null || true
    coverage report --show-missing --fail-under=50
```

Note: `--cov` flags are removed from the pytest invocation. `coverage report` (after `combine`) is the single authoritative report. Running both pytest-cov and `coverage combine+report` would produce two conflicting outputs — pytest-cov seeing only the main process (~20%) followed by the combined report (~60-75%).

**Coverage threshold:** Set `--fail-under=50` initially. The current reported 20% is artificially low because subprocess invocations weren't measured. After enabling subprocess measurement, expected true coverage is 60–75%. Start the gate at 50% (conservative) and raise after confirming the baseline.

**Edge Cases:**
- `coverage` not installed → `COVERAGE_PROCESS_START` is ignored by child processes; `coverage combine` prints "no data to combine" (exit 1); `|| true` suppresses it; `coverage report` fails with "no data" — Makefile test-unit fails loudly. This is correct behavior: the tool is required. Add `python3 -m coverage --version` as a pre-check in `make setup`.
- `sitecustomize` hook not installed → subprocess processes don't auto-measure. Fix: `python3 -m coverage sitecustomize` must be run after installing coverage. Add to `make setup` as well.
- Parallel test runs (if ever added) → `parallel=True` + `coverage combine` handles this correctly; each process writes its own `.coverage.PID` file.
- `.coverage.*` files accumulate between runs → `coverage combine` re-reads all; add `coverage erase` at the start of `test-unit` to ensure clean slate.
- `sigterm = True` in `.coveragerc` → ensures coverage data is flushed if a hook subprocess is killed by SIGTERM (e.g., timeout); without this, killed processes leave incomplete data files.

**Setup change:**
Update `make setup` to:
```makefile
setup: ## Install git hooks and coverage sitecustomize (run once after cloning)
    git config core.hooksPath .githooks
    pip3 install pytest-cov coverage
    python3 -m coverage --version
    python3 -m coverage sitecustomize
    @echo "Git hooks + coverage sitecustomize installed"
```

**Out of Scope:**
- Migrating hook tests from subprocess to import-based — larger change, separate decision
- Adding branch coverage (`branch=True`) — start with line coverage, add later
- Running coverage on `tests/` themselves — only `hooks/` is the target
- Setting coverage threshold above 50% in this item — threshold will be raised in a follow-up once baseline is confirmed
- HTML coverage report — `term-missing` in Makefile is sufficient for now
