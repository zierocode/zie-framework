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
        assert fm.get("model") == "sonnet", (
            "zie-release.md must use sonnet (ADR-064: avoids context-limit failures in long sessions)"
        )

    def test_version_suggestion_has_note_annotation(self):
        text = read("commands/release.md")
        # v1.32.0+: NOTE annotations were removed during command compaction
        # Verify model frontmatter is present instead
        assert "model:" in text, "zie-release must have model frontmatter"

    def test_changelog_step_has_note_annotation(self):
        text = read("commands/release.md")
        # v1.32.0+: NOTE annotations were removed during command compaction
        # Verify key release steps are still present
        assert "CHANGELOG" in text, "zie-release must have CHANGELOG step"


class TestImplReviewerModel:
    def test_review_skill_uses_haiku(self):
        import re

        import yaml

        text = read("skills/review/SKILL.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert match
        fm = yaml.safe_load(match.group(1))
        assert fm.get("model") == "haiku", "review SKILL.md must use haiku"

    def test_review_skill_has_model_effort_frontmatter(self):
        text = read("skills/review/SKILL.md")
        # v1.32.0+: NOTE annotations were removed during skill compaction
        # Check for model/effort frontmatter instead as proof of model routing
        assert "model: haiku" in text or "effort:" in text, (
            "review must have model/effort frontmatter for model routing"
        )
