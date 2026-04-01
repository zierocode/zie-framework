"""Tests for make test-fast and make test-ci Makefile targets."""
import subprocess


def _make(target, dry_run=True):
    cmd = ["make", "--dry-run", target] if dry_run else ["make", target]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_test_fast_target_exists():
    result = _make("test-fast")
    assert result.returncode == 0, f"make test-fast missing: {result.stderr}"


def test_test_ci_target_exists():
    result = _make("test-ci")
    assert result.returncode == 0, f"make test-ci missing: {result.stderr}"


def test_test_fast_invokes_script():
    result = _make("test-fast")
    assert "test_fast.sh" in result.stdout, "test-fast should invoke scripts/test_fast.sh"


def test_test_ci_runs_full_suite():
    result = _make("test-ci")
    assert "pytest" in result.stdout, "test-ci should invoke pytest"
    assert "fail-under=" in result.stdout, "test-ci must enforce coverage gate"


def test_help_lists_test_fast():
    result = subprocess.run(["make", "help"], capture_output=True, text=True)
    # make help shows descriptions (format: "Filename  Description")
    assert "Fast TDD feedback" in result.stdout or "test-fast" in result.stdout


def test_help_lists_test_ci():
    result = subprocess.run(["make", "help"], capture_output=True, text=True)
    assert "coverage gate" in result.stdout or "test-ci" in result.stdout


def test_test_target_unchanged():
    result = _make("test")
    assert result.returncode == 0
    assert "test-unit" in result.stdout or "pytest" in result.stdout


def test_clean_removes_coverage_file():
    result = _make("clean")
    assert ".coverage" in result.stdout, \
        "make clean must remove .coverage files"


def test_clean_removes_htmlcov():
    result = _make("clean")
    assert "htmlcov" in result.stdout, \
        "make clean must remove htmlcov/ directory"


def test_clean_removes_coverage_xml():
    result = _make("clean")
    assert "coverage.xml" in result.stdout, \
        "make clean must remove coverage.xml"
