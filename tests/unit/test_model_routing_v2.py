"""Tests for model-routing-v2: haiku downgrade for zie-release and impl-reviewer."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


class TestZieReleaseModel:
    def test_zie_release_uses_haiku(self):
        import re, yaml
        text = read("commands/zie-release.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert match
        fm = yaml.safe_load(match.group(1))
        assert fm.get("model") == "haiku", "zie-release.md must use haiku"

    def test_version_suggestion_has_sonnet_annotation(self):
        text = read("commands/zie-release.md")
        assert "model: sonnet" in text, "zie-release must have inline sonnet annotation"
        assert "version" in text.lower() or "bump" in text.lower()

    def test_changelog_step_has_sonnet_annotation(self):
        text = read("commands/zie-release.md")
        # Both the version and changelog steps should have sonnet annotations
        assert text.count("model: sonnet") >= 2, \
            "zie-release must have ≥2 sonnet escalation comments (version + changelog)"


class TestImplReviewerModel:
    def test_impl_reviewer_uses_haiku(self):
        import re, yaml
        text = read("skills/impl-reviewer/SKILL.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert match
        fm = yaml.safe_load(match.group(1))
        assert fm.get("model") == "haiku", "impl-reviewer SKILL.md must use haiku"

    def test_impl_reviewer_has_escalation_comment(self):
        text = read("skills/impl-reviewer/SKILL.md")
        assert "sonnet escalation" in text.lower() or "escalate to sonnet" in text.lower(), \
            "impl-reviewer must document sonnet escalation path"
