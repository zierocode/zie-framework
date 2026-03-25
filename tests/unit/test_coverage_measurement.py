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


class TestMakefileTestUnit:
    def test_makefile_test_unit_has_coverage_erase(self):
        """test-unit target must call coverage erase for a clean slate."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
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


class TestMakefileSetup:
    def _makefile_content(self) -> str:
        """Combined content of Makefile + Makefile.local (if present)."""
        content = (REPO_ROOT / "Makefile").read_text()
        local = REPO_ROOT / "Makefile.local"
        if local.exists():
            content += "\n" + local.read_text()
        return content

    def test_makefile_setup_has_coverage_version_check(self):
        """setup target must verify coverage is installed via --version check."""
        assert "coverage --version" in self._makefile_content(), (
            "setup target must call 'python3 -m coverage --version' in Makefile or Makefile.local"
        )

    def test_makefile_setup_has_coverage_sitecustomize(self):
        """setup target must install the coverage sitecustomize subprocess hook."""
        assert "coverage sitecustomize" in self._makefile_content(), (
            "setup target must call 'python3 -m coverage sitecustomize' in Makefile or Makefile.local"
        )
