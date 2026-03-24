"""Smoke-test the components registry stays current."""
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMPONENTS = os.path.join(
    REPO_ROOT, "zie-framework", "project", "components.md"
)


class TestComponentsRegistry:
    def _content(self):
        with open(COMPONENTS) as f:
            return f.read()

    def test_failure_context_hook_present(self):
        assert "failure-context.py" in self._content(), (
            "failure-context.py missing from components.md Hooks table"
        )

    def test_posttoolusefailure_event_documented(self):
        assert "PostToolUseFailure" in self._content()
