"""Standards compliance tests: log prefixes, documentation, notification-log."""

import re
from pathlib import Path

HOOKS_DIR = Path(__file__).parents[2] / "hooks"
BAD_PREFIX = re.compile(r"\[zie\] warning:")


class TestHookLogPrefix:
    def test_no_old_zie_warning_prefix_in_hooks(self):
        """No hook must use the deprecated '[zie] warning:' prefix."""
        violations = []
        for hook in sorted(HOOKS_DIR.glob("*.py")):
            text = hook.read_text()
            for lineno, line in enumerate(text.splitlines(), 1):
                if BAD_PREFIX.search(line):
                    violations.append(f"{hook.name}:{lineno}: {line.strip()}")
        assert not violations, (
            "Found deprecated '[zie] warning:' prefix in hooks:\n"
            + "\n".join(violations)
            + "\nReplace with '[zie-framework] <hook-name>:'"
        )


class TestDocumentation:
    def test_claude_md_documents_integration_test_exclusion(self):
        """CLAUDE.md must document that make test-unit excludes integration tests."""
        root = Path(__file__).parents[2]
        text = (root / "CLAUDE.md").read_text()
        assert "integration" in text.lower() and "test-unit" in text, (
            "CLAUDE.md must explain that make test-unit excludes integration tests"
        )

    def test_makefile_has_integration_exclusion_comment(self):
        """Makefile must have a comment documenting integration test exclusion."""
        root = Path(__file__).parents[2]
        text = (root / "Makefile").read_text()
        assert "integration" in text and "test-unit" in text, (
            "Makefile must have a comment documenting integration test exclusion"
        )


class TestNotificationLogProjectName:
    def test_notification_log_uses_safe_project_name(self):
        """notification-log.py must call safe_project_name() on cwd.name."""
        root = Path(__file__).parents[2]
        text = (root / "hooks" / "notification-log.py").read_text()
        assert "safe_project_name" in text, (
            "notification-log.py must import and use safe_project_name() for consistency with other hooks"
        )
