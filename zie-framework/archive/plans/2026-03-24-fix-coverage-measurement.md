---
approved: true
approved_at: 2026-03-24
backlog: backlog/fix-coverage-measurement.md
spec: specs/2026-03-24-fix-coverage-measurement-design.md
---

# Fix Coverage Measurement Infrastructure — Implementation Plan

**Goal:** Replace the broken pytest-cov measurement (which misses all subprocess-spawned hooks) with `coverage.py` subprocess measurement via `COVERAGE_PROCESS_START`, so the 14 hooks currently showing 0% are correctly measured and a coverage gate can be enforced.
**Architecture:** Add `.coveragerc` at project root with `parallel=True` and `source=hooks`. Update `make test-unit` to set `COVERAGE_PROCESS_START` before pytest, then run `coverage combine` + `coverage report --fail-under=50` after. Update `make setup` to install the `coverage sitecustomize` hook. Zero changes to test code or hook source.
**Tech Stack:** Python 3.x, coverage.py, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `.coveragerc` | Coverage config: source, parallel, sigterm, report, paths |
| Modify | `Makefile` | Update `test-unit` target; update `setup` target |
| Create | `tests/unit/test_coverage_measurement.py` | Verify `.coveragerc` exists and has required keys |

---

## Task 1: `.coveragerc` config file

**Acceptance Criteria:**
- `.coveragerc` exists at project root
- Contains `[run]` section with `source = hooks`, `parallel = True`, `sigterm = True`
- Contains `[report]` section with `show_missing = True`, `skip_covered = False`
- Contains `[paths]` section with `hooks/` mapping

**Files:**
- Create: `.coveragerc`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Create tests/unit/test_coverage_measurement.py

  """Verify .coveragerc exists and has required keys for subprocess coverage measurement."""
  import configparser
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  COVERAGERC = REPO_ROOT / ".coveragerc"


  class TestCoverageRc:
      def test_coveragerc_exists(self):
          """Project root must have a .coveragerc file."""
          assert COVERAGERC.exists(), (
              f".coveragerc not found at {COVERAGERC} — create it to enable subprocess coverage"
          )

      def test_coveragerc_run_source(self):
          """[run] source must be set to hooks."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.get("run", "source", fallback=None) == "hooks", (
              "[run] source must be 'hooks' in .coveragerc"
          )

      def test_coveragerc_run_parallel(self):
          """[run] parallel must be True for subprocess measurement."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.get("run", "parallel", fallback=None) == "True", (
              "[run] parallel must be 'True' in .coveragerc"
          )

      def test_coveragerc_run_sigterm(self):
          """[run] sigterm must be True to flush data on SIGTERM."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.get("run", "sigterm", fallback=None) == "True", (
              "[run] sigterm must be 'True' in .coveragerc"
          )

      def test_coveragerc_report_show_missing(self):
          """[report] show_missing must be True."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.get("report", "show_missing", fallback=None) == "True", (
              "[report] show_missing must be 'True' in .coveragerc"
          )

      def test_coveragerc_report_skip_covered(self):
          """[report] skip_covered must be False."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.get("report", "skip_covered", fallback=None) == "False", (
              "[report] skip_covered must be 'False' in .coveragerc"
          )

      def test_coveragerc_paths_hooks(self):
          """[paths] section must contain a hooks key mapping to hooks/."""
          cfg = configparser.ConfigParser()
          cfg.read(COVERAGERC)
          assert cfg.has_option("paths", "hooks"), (
              "[paths] hooks key not found in .coveragerc"
          )
          assert "hooks/" in cfg.get("paths", "hooks"), (
              "[paths] hooks value must include 'hooks/' in .coveragerc"
          )
  ```

  Run: `make test-unit` — must FAIL (`.coveragerc` does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```ini
  # Create .coveragerc at project root

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

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No refactor needed — this is a new config file with no logic to simplify.

  Run: `make test-unit` — still PASS

---

## Task 2: Update `make test-unit` in Makefile

**Acceptance Criteria:**
- `make test-unit` runs `coverage erase` before pytest
- pytest is invoked with `COVERAGE_PROCESS_START=$(CURDIR)/.coveragerc` set in the environment
- No `--cov` flags on the pytest invocation
- `coverage combine 2>/dev/null || true` runs after pytest
- `coverage report --show-missing --fail-under=50` runs after combine

**Files:**
- Modify: `Makefile`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_coverage_measurement.py

  class TestMakefileTestUnit:
      def test_makefile_test_unit_has_coverage_erase(self):
          """test-unit target must call coverage erase for a clean slate."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          # Find the test-unit block
          assert "coverage erase" in content, (
              "test-unit target must call 'coverage erase' in Makefile"
          )

      def test_makefile_test_unit_has_coverage_process_start(self):
          """test-unit target must set COVERAGE_PROCESS_START before pytest."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "COVERAGE_PROCESS_START" in content, (
              "test-unit target must set COVERAGE_PROCESS_START in Makefile"
          )

      def test_makefile_test_unit_no_cov_flags(self):
          """test-unit target must NOT use --cov flags (coverage report is the authority)."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          # Find test-unit block lines only
          in_test_unit = False
          for line in content.splitlines():
              if line.startswith("test-unit:"):
                  in_test_unit = True
              elif in_test_unit and line and not line[0].isspace() and not line.startswith("\t"):
                  break
              elif in_test_unit:
                  assert "--cov" not in line, (
                      f"test-unit must not use --cov flags (conflicts with coverage combine): {line!r}"
                  )

      def test_makefile_test_unit_has_coverage_combine(self):
          """test-unit target must run coverage combine after pytest."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "coverage combine" in content, (
              "test-unit target must call 'coverage combine' in Makefile"
          )

      def test_makefile_test_unit_has_coverage_report_fail_under(self):
          """test-unit target must run coverage report with --fail-under=50."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "coverage report" in content and "--fail-under=50" in content, (
              "test-unit target must call 'coverage report --fail-under=50' in Makefile"
          )
  ```

  Run: `make test-unit` — must FAIL (current `test-unit` has none of these)

---

- [ ] **Step 2: Implement (GREEN)**

  ```makefile
  # In Makefile, replace the existing test-unit target:

  # BEFORE:
  test-unit: ## Fast unit tests (run constantly during /zie-build)
  	python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"

  # AFTER:
  test-unit: ## Fast unit tests with subprocess coverage measurement
  	python3 -m coverage erase
  	COVERAGE_PROCESS_START=$(CURDIR)/.coveragerc \
  	    python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"
  	python3 -m coverage combine 2>/dev/null || true
  	python3 -m coverage report --show-missing --fail-under=50
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No further simplification needed. The `2>/dev/null || true` on `coverage combine` is
  intentional — it suppresses the "no data to combine" message on a clean run without
  breaking the target. This matches the pattern already used in the codebase.

  Run: `make test-unit` — still PASS

---

## Task 3: Update `make setup` in Makefile

**Acceptance Criteria:**
- `make setup` installs `pytest-cov` and `coverage` via pip
- `make setup` runs `python3 -m coverage --version` as a presence check
- `make setup` runs `python3 -m coverage sitecustomize` to install the subprocess hook
- Echo confirms both git hooks and coverage sitecustomize are installed

**Files:**
- Modify: `Makefile`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_coverage_measurement.py

  class TestMakefileSetup:
      def test_makefile_setup_has_coverage_version_check(self):
          """setup target must verify coverage is installed via --version check."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "coverage --version" in content, (
              "setup target must call 'python3 -m coverage --version' in Makefile"
          )

      def test_makefile_setup_has_coverage_sitecustomize(self):
          """setup target must install the coverage sitecustomize subprocess hook."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "coverage sitecustomize" in content, (
              "setup target must call 'python3 -m coverage sitecustomize' in Makefile"
          )
  ```

  Run: `make test-unit` — must FAIL (current `setup` target has neither)

---

- [ ] **Step 2: Implement (GREEN)**

  ```makefile
  # In Makefile, replace the existing setup target:

  # BEFORE:
  setup: ## Install git hooks (run once after cloning)
  	git config core.hooksPath .githooks
  	@echo "Git hooks installed from .githooks/"

  # AFTER:
  setup: ## Install git hooks and coverage sitecustomize (run once after cloning)
  	git config core.hooksPath .githooks
  	pip3 install pytest-cov coverage
  	python3 -m coverage --version
  	python3 -m coverage sitecustomize
  	@echo "Git hooks + coverage sitecustomize installed"
  ```

  Run: `make test-unit` — must PASS
  Run: `make setup` — must print version and confirm sitecustomize installed

---

- [ ] **Step 3: Refactor**

  No refactor needed. `pip3 install pytest-cov coverage` is idempotent. The
  `python3 -m coverage --version` line acts as a fast sanity check that the install
  succeeded and will fail loudly if coverage is missing — which is the intended behavior
  per the spec edge-case analysis.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add .coveragerc Makefile tests/unit/test_coverage_measurement.py && git commit -m "fix: fix-coverage-measurement — add .coveragerc and subprocess coverage measurement to make test-unit"`
