"""Structural test: requirements-dev.txt must use ~= pinning for all deps."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
REQ_FILE = REPO_ROOT / "requirements-dev.txt"


class TestDepPinning:
    def test_requirements_dev_exists(self):
        assert REQ_FILE.exists(), "requirements-dev.txt not found"

    def test_all_deps_use_compatible_release_pinning(self):
        lines = REQ_FILE.read_text().splitlines()
        dep_lines = [
            line for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        assert dep_lines, "requirements-dev.txt has no dependency lines"
        bad_lines = [
            line for line in dep_lines
            if not re.search(r"~=\d", line)
        ]
        assert bad_lines == [], (
            f"Dependencies not using ~= pinning: {bad_lines}\n"
            "All deps must use ~=X.Y.Z (compatible-release) pinning."
        )

    def test_no_exact_pin(self):
        content = REQ_FILE.read_text()
        dep_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        exact_pins = [line for line in dep_lines if re.search(r"==\d", line)]
        assert exact_pins == [], (
            f"Exact pins (==) found; use ~= instead: {exact_pins}"
        )

    def test_no_lower_bound_only_pin(self):
        content = REQ_FILE.read_text()
        dep_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        lower_bound_only = [line for line in dep_lines if re.search(r">=\d", line)]
        assert lower_bound_only == [], (
            f"Lower-bound-only pins (>=) found; use ~= instead: {lower_bound_only}"
        )
