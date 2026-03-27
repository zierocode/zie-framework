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
        assert any(r.strip() == "make test-unit" for r in run_values), \
            "make test-unit step missing or has unexpected extra flags"

    def test_no_continue_on_error_on_make_test(self):
        for step in self._steps():
            if step.get("run", "").strip() == "make test-unit":
                assert step.get("continue-on-error") is not True, \
                    "make test-unit step must not have continue-on-error: true"
                return
