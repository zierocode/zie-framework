import subprocess
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
PROJECT_MD = REPO_ROOT / "zie-framework" / "PROJECT.md"


def run_make(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", "-C", str(REPO_ROOT)] + args,
        capture_output=True,
        text=True,
    )


class TestMakeBump:
    def setup_method(self, _method):
        """Capture original state before each test."""
        self._original_version = VERSION_FILE.read_text().strip()
        self._original_project_md = PROJECT_MD.read_text()

    def teardown_method(self, _method):
        """Restore VERSION, plugin.json, and PROJECT.md after each test."""
        VERSION_FILE.write_text(self._original_version + "\n")
        data = json.loads(PLUGIN_JSON.read_text())
        data["version"] = self._original_version
        PLUGIN_JSON.write_text(json.dumps(data, indent=2) + "\n")
        PROJECT_MD.write_text(self._original_project_md)

    def test_bump_updates_version_file(self):
        result = run_make(["bump", "NEW=1.99.0"])
        assert result.returncode == 0, result.stderr
        assert VERSION_FILE.read_text().strip() == "1.99.0"

    def test_bump_updates_plugin_json(self):
        result = run_make(["bump", "NEW=1.99.0"])
        assert result.returncode == 0, result.stderr
        data = json.loads(PLUGIN_JSON.read_text())
        assert data["version"] == "1.99.0"

    def test_bump_prints_confirmation(self):
        result = run_make(["bump", "NEW=1.99.0"])
        assert result.returncode == 0, result.stderr
        assert "1.99.0" in result.stdout

    def test_bump_without_new_exits_nonzero(self):
        result = run_make(["bump"])
        assert result.returncode != 0
        # Files must not be modified — version unchanged
        assert VERSION_FILE.read_text().strip() == self._original_version

    def test_bump_invalid_semver_exits_nonzero(self):
        result = run_make(["bump", "NEW=not-a-version"])
        assert result.returncode != 0
        assert VERSION_FILE.read_text().strip() == self._original_version

    def test_bump_does_not_modify_other_makefile_targets(self):
        """Regression: make help still works after bump is added."""
        result = run_make(["help"])
        assert result.returncode == 0
