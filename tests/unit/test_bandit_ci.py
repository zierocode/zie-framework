"""Smoke test: bandit must exit 0 on hooks/ at medium severity + confidence."""
import subprocess
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
HOOKS_DIR = str(REPO_ROOT / "hooks")


class TestBanditSast:
    def test_bandit_is_importable(self):
        """bandit must be installed in the current environment."""
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            "bandit is not installed — run: pip install bandit>=1.7\n"
            + result.stderr
        )

    def test_bandit_hooks_exits_clean(self):
        """hooks/ must have zero bandit findings at medium severity + medium confidence."""
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", HOOKS_DIR, "-ll", "-q", "-c", ".bandit"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            "bandit found issues in hooks/:\n"
            + result.stdout
            + result.stderr
        )

    def _makefile_content(self) -> str:
        """Combined content of Makefile + Makefile.local (if present)."""
        content = (REPO_ROOT / "Makefile").read_text()
        local = REPO_ROOT / "Makefile.local"
        if local.exists():
            content += "\n" + local.read_text()
        return content

    def test_make_lint_bandit_target_exists(self):
        """Makefile or Makefile.local must define a lint-bandit target."""
        assert "lint-bandit:" in self._makefile_content(), \
            "lint-bandit target not found in Makefile or Makefile.local"

    def test_make_lint_calls_lint_bandit(self):
        """The lint target must depend on or call lint-bandit."""
        content = self._makefile_content()
        for line in content.splitlines():
            if line.startswith("lint:") or line.startswith("lint "):
                assert "lint-bandit" in line, (
                    f"lint target does not call lint-bandit: {line!r}"
                )
                break
        else:
            raise AssertionError("lint target not found in Makefile or Makefile.local")


class TestPreCommitBanditIntegration:
    def test_pre_commit_calls_lint_bandit(self):
        """pre-commit hook script must contain a make lint-bandit invocation."""
        pre_commit = REPO_ROOT / ".githooks" / "pre-commit"
        content = pre_commit.read_text()
        assert "lint-bandit" in content, (
            "pre-commit hook does not call lint-bandit"
        )

    def test_pre_commit_has_bandit_install_guard(self):
        """pre-commit hook must guard bandit availability with command -v or equivalent."""
        pre_commit = REPO_ROOT / ".githooks" / "pre-commit"
        content = pre_commit.read_text()
        assert "bandit" in content, "pre-commit does not mention bandit"
        assert (
            "command -v bandit" in content or "pip install bandit" in content
        ), "pre-commit hook lacks a bandit availability guard or install hint"
