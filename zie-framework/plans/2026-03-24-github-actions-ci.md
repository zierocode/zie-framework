---
approved: false
approved_at: ~
backlog: backlog/github-actions-ci.md
spec: specs/2026-03-24-github-actions-ci-design.md
---

# CI/CD via GitHub Actions — Implementation Plan

**Goal:** Create `.github/workflows/ci.yml` so that every push to `main`/`dev`
and every pull request targeting either branch automatically runs `make test`,
producing a visible green/red commit status.

**Architecture:** Single YAML file addition. No new Python code, no new secrets.
The workflow installs pytest + bandit via pip, then runs `make test` (which
covers `test-unit` + `lint-md`). `lint-md` calls `npx markdownlint-cli` — npx
fetches it at runtime, so no separate npm install step is needed.

**Tech Stack:** GitHub Actions YAML, Python (version from `.python-version`), pytest, bandit, markdownlint-cli (npx)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `.github/workflows/ci.yml` | CI workflow: trigger, setup, install, test |
| Create | `tests/unit/test_ci_workflow.py` | Validate workflow YAML structure |

---

## Task 1: Create `.github/workflows/ci.yml`

<!-- depends_on: none -->

**Acceptance Criteria:**

- `.github/workflows/ci.yml` exists and is valid YAML
- `on.push.branches` includes `main` and `dev`
- `on.pull_request.branches` includes `main` and `dev`
- Job uses `ubuntu-latest`
- `actions/checkout@v4` step is present
- `actions/setup-python@v5` step is present with `python-version-file: ".python-version"`
- `pip install pytest bandit` step is present
- `make test` step is present
- `make test` failure causes the workflow to fail (default behaviour — no
  `continue-on-error`)

**Files:**

- Create: `.github/workflows/ci.yml`
- Create: `tests/unit/test_ci_workflow.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_ci_workflow.py
  import yaml
  from pathlib import Path

  WORKFLOW_PATH = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"


  def load_workflow() -> dict:
      assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"
      return yaml.safe_load(WORKFLOW_PATH.read_text())


  class TestCiWorkflowExists:
      def test_file_exists(self):
          assert WORKFLOW_PATH.exists()

      def test_file_is_valid_yaml(self):
          data = load_workflow()
          assert isinstance(data, dict)


  class TestCiWorkflowTriggers:
      def test_push_trigger_present(self):
          data = load_workflow()
          assert "push" in data["on"], "on.push trigger missing"

      def test_push_includes_main(self):
          data = load_workflow()
          branches = data["on"]["push"]["branches"]
          assert "main" in branches, "on.push.branches must include main"

      def test_push_includes_dev(self):
          data = load_workflow()
          branches = data["on"]["push"]["branches"]
          assert "dev" in branches, "on.push.branches must include dev"

      def test_pull_request_trigger_present(self):
          data = load_workflow()
          assert "pull_request" in data["on"], "on.pull_request trigger missing"

      def test_pull_request_includes_main(self):
          data = load_workflow()
          branches = data["on"]["pull_request"]["branches"]
          assert "main" in branches, "on.pull_request.branches must include main"

      def test_pull_request_includes_dev(self):
          data = load_workflow()
          branches = data["on"]["pull_request"]["branches"]
          assert "dev" in branches, "on.pull_request.branches must include dev"


  class TestCiWorkflowJob:
      def test_jobs_key_present(self):
          data = load_workflow()
          assert "jobs" in data

      def test_test_job_present(self):
          data = load_workflow()
          assert "test" in data["jobs"], "jobs.test missing"

      def test_runs_on_ubuntu_latest(self):
          data = load_workflow()
          assert data["jobs"]["test"]["runs-on"] == "ubuntu-latest"

      def test_steps_present(self):
          data = load_workflow()
          steps = data["jobs"]["test"]["steps"]
          assert isinstance(steps, list)
          assert len(steps) > 0


  class TestCiWorkflowSteps:
      def _steps(self) -> list:
          return load_workflow()["jobs"]["test"]["steps"]

      def test_checkout_step_present(self):
          uses_values = [s.get("uses", "") for s in self._steps()]
          assert any("actions/checkout" in u for u in uses_values), \
              "checkout step missing"

      def test_checkout_uses_v4(self):
          uses_values = [s.get("uses", "") for s in self._steps()]
          assert any(u == "actions/checkout@v4" for u in uses_values), \
              "checkout must use actions/checkout@v4"

      def test_setup_python_step_present(self):
          uses_values = [s.get("uses", "") for s in self._steps()]
          assert any("actions/setup-python" in u for u in uses_values), \
              "setup-python step missing"

      def test_setup_python_uses_v5(self):
          uses_values = [s.get("uses", "") for s in self._steps()]
          assert any(u == "actions/setup-python@v5" for u in uses_values), \
              "setup-python must use actions/setup-python@v5"

      def test_python_version_file_used(self):
          for step in self._steps():
              if step.get("uses", "").startswith("actions/setup-python"):
                  version_file = step.get("with", {}).get("python-version-file")
                  assert version_file == ".python-version", \
                      f"setup-python must use python-version-file: '.python-version', got '{version_file}'"
                  return
          raise AssertionError("setup-python step not found")

      def test_pip_install_step_present(self):
          run_values = [s.get("run", "") for s in self._steps()]
          assert any("pip install" in r for r in run_values), \
              "pip install step missing"

      def test_pip_installs_pytest(self):
          run_values = [s.get("run", "") for s in self._steps()]
          assert any("pytest" in r for r in run_values), \
              "pip install must include pytest"

      def test_pip_installs_bandit(self):
          run_values = [s.get("run", "") for s in self._steps()]
          assert any("bandit" in r for r in run_values), \
              "pip install must include bandit"

      def test_make_test_step_present(self):
          run_values = [s.get("run", "") for s in self._steps()]
          assert any(r.strip() == "make test" for r in run_values), \
              "make test step missing or has unexpected extra flags"

      def test_no_continue_on_error_on_make_test(self):
          for step in self._steps():
              if step.get("run", "").strip() == "make test":
                  assert step.get("continue-on-error") is not True, \
                      "make test step must not have continue-on-error: true"
                  return
  ```

  Run: `make test-unit` — must **FAIL** (`.github/workflows/ci.yml` does not
  exist yet)

- [ ] **Step 2: Implement (GREEN)**

  First, ensure `.python-version` exists at repo root. Check with `cat .python-version`. If it does not exist, create it with the project's current Python version (check `python3 --version` and write just the version string, e.g. `3.13`):
  ```bash
  python3 --version  # e.g. "Python 3.13.2"
  echo "3.13" > .python-version  # if file does not exist
  ```

  Create `.github/workflows/ci.yml`:

  ```yaml
  name: CI

  on:
    push:
      branches:
        - main
        - dev
    pull_request:
      branches:
        - main
        - dev

  jobs:
    test:
      runs-on: ubuntu-latest

      steps:
        - uses: actions/checkout@v4

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version-file: ".python-version"

        - name: Install dependencies
          run: pip install pytest bandit

        - name: Run tests
          run: make test
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  Review the workflow for clarity:

  - Confirm step names are present and descriptive (`name:` on each step)
  - Confirm no extra keys (caching, matrix, env vars) have crept in — out of
    scope per spec
  - Confirm YAML indentation is consistent (2 spaces throughout)

  Run: `make test-unit` — still **PASS**

---

*Commit: `git add .github/workflows/ci.yml tests/unit/test_ci_workflow.py && git commit -m "feat: github-actions-ci"`*
