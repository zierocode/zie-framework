"""Tests for model-routing-v2: haiku downgrade for zie-release and impl-review."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


class TestZieReleaseModel:
    def test_zie_release_uses_sonnet(self):
        import re

        import yaml
        text = read("commands/release.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert match
        fm = yaml.safe_load(match.group(1))
        assert fm.get("model") == "sonnet", "zie-release.md must use sonnet (ADR-064: avoids context-limit failures in long sessions)"

    def test_version_suggestion_has_note_annotation(self):
        text = read("commands/release.md")
        assert "<!-- NOTE:" in text, "zie-release must have NOTE annotation"

    def test_changelog_step_has_note_annotation(self):
        text = read("commands/release.md")
        assert text.count("<!-- NOTE:") >= 2, \
            "zie-release must have ≥2 NOTE comments (version + changelog)"


class TestImplReviewerModel:
    def test_impl_reviewer_uses_haiku(self):
        import re

        import yaml
        text = read("skills/impl-review/SKILL.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert match
        fm = yaml.safe_load(match.group(1))
        assert fm.get("model") == "haiku", "impl-review SKILL.md must use haiku"

    def test_impl_reviewer_has_note_annotation(self):
        text = read("skills/impl-review/SKILL.md")
        assert "<!-- NOTE:" in text, \
            "impl-review must have NOTE annotation"
