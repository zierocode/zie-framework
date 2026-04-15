"""Tests for skill auto-inject: phase-to-skill mapping and context injection."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_skill_inject import inject_skill_context, DEFAULT_SKILL_MAPPING, MAX_INJECT_CHARS
from pathlib import Path


class TestDefaultMapping:
    def test_spec_maps_to_spec_reviewer(self):
        assert DEFAULT_SKILL_MAPPING["spec"] == "spec-review"

    def test_plan_maps_to_write_plan(self):
        assert DEFAULT_SKILL_MAPPING["plan"] == "write-plan"

    def test_implement_maps_to_impl_reviewer(self):
        assert DEFAULT_SKILL_MAPPING["implement"] == "impl-review"


class TestInjectSkillContext:
    def test_returns_none_when_no_config(self, tmp_path):
        result = inject_skill_context("implement", tmp_path)
        assert result is None

    def test_returns_none_when_disabled(self, tmp_path):
        (tmp_path / "zie-framework").mkdir()
        config = {"skill_auto_inject": {"enabled": False}}
        (tmp_path / "zie-framework" / ".config").write_text(json.dumps(config))
        result = inject_skill_context("implement", tmp_path)
        assert result is None

    def test_returns_skill_content_for_valid_stage(self, tmp_path):
        # Setup project structure
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        config = {"skill_auto_inject": {"enabled": True}}
        (zf / ".config").write_text(json.dumps(config))

        # Create a skill file
        skill_dir = tmp_path / "skills" / "impl-review"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Impl Reviewer\n\nReview code changes.")

        result = inject_skill_context("implement", tmp_path)
        assert result is not None
        assert "Impl Reviewer" in result

    def test_returns_none_for_unknown_stage(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        config = {"skill_auto_inject": {"enabled": True}}
        (zf / ".config").write_text(json.dumps(config))

        result = inject_skill_context("unknown_stage", tmp_path)
        assert result is None

    def test_custom_mapping_overrides_default(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        config = {
            "skill_auto_inject": {
                "enabled": True,
                "mapping": {"spec": "custom-reviewer"},
            }
        }
        (zf / ".config").write_text(json.dumps(config))

        # Create custom skill file
        skill_dir = tmp_path / "skills" / "custom-reviewer"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Custom Reviewer\n\nCustom content.")

        result = inject_skill_context("spec", tmp_path)
        assert result is not None
        assert "Custom Reviewer" in result

    def test_missing_skill_returns_none(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        config = {"skill_auto_inject": {"enabled": True}}
        (zf / ".config").write_text(json.dumps(config))

        result = inject_skill_context("implement", tmp_path)
        assert result is None

    def test_content_truncated_at_max(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        config = {"skill_auto_inject": {"enabled": True}}
        (zf / ".config").write_text(json.dumps(config))

        # Create a long skill file
        skill_dir = tmp_path / "skills" / "impl-review"
        skill_dir.mkdir(parents=True)
        long_content = "# Impl Reviewer\n\n" + ("A" * 5000)
        (skill_dir / "SKILL.md").write_text(long_content)

        result = inject_skill_context("implement", tmp_path)
        assert result is not None
        assert len(result) <= MAX_INJECT_CHARS + 50  # Allow for truncation marker + header

    def test_non_sdlc_project_returns_none(self, tmp_path):
        # No zie-framework directory
        result = inject_skill_context("implement", tmp_path)
        assert result is None