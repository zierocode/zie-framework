"""Tests for init-scan-prompt-extract: template extraction from init.md."""

import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INIT_MD = os.path.join(REPO_ROOT, "commands", "init.md")
TEMPLATE = os.path.join(REPO_ROOT, "templates", "init-scan-prompt.md")


class TestTemplateExists:
    def test_template_file_exists(self):
        assert os.path.isfile(TEMPLATE), "templates/init-scan-prompt.md must exist"

    def test_init_md_has_reference_line(self):
        with open(INIT_MD) as f:
            content = f.read()
        assert "templates/init-scan-prompt.md" in content, (
            "commands/init.md must reference templates/init-scan-prompt.md"
        )

    def test_init_md_does_not_contain_inline_prompt_body(self):
        """The verbatim prompt block must not remain inline in init.md."""
        with open(INIT_MD) as f:
            content = f.read()
        # A distinctive string from inside the extracted prompt body
        assert "The parent parser will extract JSON from the first" not in content, (
            "Inline prompt body must be extracted to templates/init-scan-prompt.md"
        )

    def test_template_contains_prompt_body(self):
        with open(TEMPLATE) as f:
            content = f.read()
        assert "The parent parser will extract JSON from the first" in content, (
            "templates/init-scan-prompt.md must contain the extracted prompt body"
        )
