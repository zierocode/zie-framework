"""Structural test: zie-implement must invoke context skill for context bundle."""

from pathlib import Path

ZIE_IMPLEMENT = Path(__file__).parents[2] / "commands" / "implement.md"


def test_context_skill_invoked():
    """Context bundle is loaded via Skill(zie-framework:context) invocation."""
    assert "Skill(zie-framework:context" in ZIE_IMPLEMENT.read_text(), (
        "implement.md must invoke Skill(zie-framework:context) for context bundle"
    )


def test_context_bundle_passed_to_reviewer():
    """context_bundle must be passed to impl-review."""
    assert "context_bundle" in ZIE_IMPLEMENT.read_text(), (
        "implement.md must reference context_bundle for reviewer"
    )