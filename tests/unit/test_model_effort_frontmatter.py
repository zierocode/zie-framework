"""Tests for model: and effort: frontmatter fields in skills and commands."""
import re
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def parse_frontmatter(rel_path: str) -> dict:
    """Extract and parse YAML frontmatter from a markdown file.

    Returns the parsed dict. Raises AssertionError if no frontmatter block
    is found, or yaml.YAMLError if the block is malformed.
    """
    text = (REPO_ROOT / rel_path).read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"No frontmatter block found in {rel_path}"
    return yaml.safe_load(match.group(1))


class TestHaikuLowFrontmatter:
    """Task 1 — model:haiku + effort:low on reviewer skills and zie-status."""

    def test_zie_status_model_haiku(self):
        fm = parse_frontmatter("commands/zie-status.md")
        assert fm.get("model") == "haiku", (
            "commands/zie-status.md must have model: haiku"
        )

    def test_zie_status_effort_low(self):
        fm = parse_frontmatter("commands/zie-status.md")
        assert fm.get("effort") == "low", (
            "commands/zie-status.md must have effort: low"
        )

    def test_spec_reviewer_model_haiku(self):
        fm = parse_frontmatter("skills/spec-reviewer/SKILL.md")
        assert fm.get("model") == "haiku", (
            "skills/spec-reviewer/SKILL.md must have model: haiku"
        )

    def test_spec_reviewer_effort_low(self):
        fm = parse_frontmatter("skills/spec-reviewer/SKILL.md")
        assert fm.get("effort") == "low", (
            "skills/spec-reviewer/SKILL.md must have effort: low"
        )

    def test_plan_reviewer_model_haiku(self):
        fm = parse_frontmatter("skills/plan-reviewer/SKILL.md")
        assert fm.get("model") == "haiku", (
            "skills/plan-reviewer/SKILL.md must have model: haiku"
        )

    def test_plan_reviewer_effort_low(self):
        fm = parse_frontmatter("skills/plan-reviewer/SKILL.md")
        assert fm.get("effort") == "low", (
            "skills/plan-reviewer/SKILL.md must have effort: low"
        )

    def test_impl_reviewer_model_haiku(self):
        fm = parse_frontmatter("skills/impl-reviewer/SKILL.md")
        assert fm.get("model") == "haiku", (
            "skills/impl-reviewer/SKILL.md must have model: haiku"
        )

    def test_impl_reviewer_effort_low(self):
        fm = parse_frontmatter("skills/impl-reviewer/SKILL.md")
        assert fm.get("effort") == "low", (
            "skills/impl-reviewer/SKILL.md must have effort: low"
        )


class TestSonnetHighFrontmatter:
    """Task 2 — model:sonnet + effort:high on spec-design, write-plan, zie-spec, zie-plan."""

    def test_spec_design_model_sonnet(self):
        fm = parse_frontmatter("skills/spec-design/SKILL.md")
        assert fm.get("model") == "sonnet", (
            "skills/spec-design/SKILL.md must have model: sonnet"
        )

    def test_spec_design_effort_high(self):
        fm = parse_frontmatter("skills/spec-design/SKILL.md")
        assert fm.get("effort") == "high", (
            "skills/spec-design/SKILL.md must have effort: high"
        )

    def test_write_plan_model_sonnet(self):
        fm = parse_frontmatter("skills/write-plan/SKILL.md")
        assert fm.get("model") == "sonnet", (
            "skills/write-plan/SKILL.md must have model: sonnet"
        )

    def test_write_plan_effort_high(self):
        fm = parse_frontmatter("skills/write-plan/SKILL.md")
        assert fm.get("effort") == "high", (
            "skills/write-plan/SKILL.md must have effort: high"
        )

    def test_zie_spec_effort_high(self):
        fm = parse_frontmatter("commands/zie-spec.md")
        assert fm.get("effort") == "high", (
            "commands/zie-spec.md must have effort: high"
        )

    def test_zie_plan_effort_high(self):
        fm = parse_frontmatter("commands/zie-plan.md")
        assert fm.get("effort") == "high", (
            "commands/zie-plan.md must have effort: high"
        )


class TestMediumFrontmatter:
    """Task 3 — effort:medium on zie-implement and zie-fix."""

    def test_zie_implement_effort_medium(self):
        fm = parse_frontmatter("commands/zie-implement.md")
        assert fm.get("effort") == "medium", (
            "commands/zie-implement.md must have effort: medium"
        )

    def test_zie_implement_no_model_pin(self):
        fm = parse_frontmatter("commands/zie-implement.md")
        assert "model" not in fm, (
            "commands/zie-implement.md must not have a model pin (session default)"
        )

    def test_zie_fix_effort_medium(self):
        fm = parse_frontmatter("commands/zie-fix.md")
        assert fm.get("effort") == "medium", (
            "commands/zie-fix.md must have effort: medium"
        )

    def test_zie_fix_no_model_pin(self):
        fm = parse_frontmatter("commands/zie-fix.md")
        assert "model" not in fm, (
            "commands/zie-fix.md must not have a model pin (session default)"
        )


class TestFrontmatterValidity:
    """Task 4 — YAML parse guard: all 10 modified files must have valid frontmatter."""

    MODIFIED_FILES = [
        "commands/zie-status.md",
        "skills/spec-reviewer/SKILL.md",
        "skills/plan-reviewer/SKILL.md",
        "skills/impl-reviewer/SKILL.md",
        "skills/spec-design/SKILL.md",
        "skills/write-plan/SKILL.md",
        "commands/zie-spec.md",
        "commands/zie-plan.md",
        "commands/zie-implement.md",
        "commands/zie-fix.md",
    ]

    def test_all_modified_files_have_valid_frontmatter(self):
        errors = []
        for rel_path in self.MODIFIED_FILES:
            try:
                parse_frontmatter(rel_path)
            except Exception as exc:
                errors.append(f"{rel_path}: {exc}")
        assert errors == [], "Frontmatter parse errors:\n" + "\n".join(errors)

    def test_all_modified_files_have_effort_key(self):
        errors = []
        for rel_path in self.MODIFIED_FILES:
            fm = parse_frontmatter(rel_path)
            if "effort" not in fm:
                errors.append(rel_path)
        assert errors == [], f"Missing 'effort' key in: {errors}"

    def test_effort_values_are_valid(self):
        valid = {"low", "medium", "high"}
        errors = []
        for rel_path in self.MODIFIED_FILES:
            fm = parse_frontmatter(rel_path)
            val = fm.get("effort")
            if val not in valid:
                errors.append(f"{rel_path}: effort={val!r}")
        assert errors == [], f"Invalid effort values: {errors}"

    def test_model_values_are_valid_when_present(self):
        valid = {"haiku", "sonnet"}
        errors = []
        for rel_path in self.MODIFIED_FILES:
            fm = parse_frontmatter(rel_path)
            val = fm.get("model")
            if val is not None and val not in valid:
                errors.append(f"{rel_path}: model={val!r}")
        assert errors == [], f"Invalid model values: {errors}"


class TestUnchangedSkillsHaveNoModelPin:
    """Task 4 — regression guard: skills marked 'No change' must not gain model/effort keys."""

    NO_CHANGE_SKILLS = [
        "skills/tdd-loop/SKILL.md",
        "skills/debug/SKILL.md",
        "skills/retro-format/SKILL.md",
        "skills/test-pyramid/SKILL.md",
        "skills/verify/SKILL.md",
    ]

    def test_no_change_skills_have_no_model_key(self):
        for rel_path in self.NO_CHANGE_SKILLS:
            path = REPO_ROOT / rel_path
            if not path.exists():
                continue  # skill may not have frontmatter at all — safe to skip
            text = path.read_text()
            match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            if not match:
                continue  # no frontmatter block — fine
            fm = yaml.safe_load(match.group(1)) or {}
            assert "model" not in fm, (
                f"{rel_path} must not have a model pin (out-of-scope per spec)"
            )

    def test_no_change_skills_have_no_effort_key(self):
        for rel_path in self.NO_CHANGE_SKILLS:
            path = REPO_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text()
            match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            if not match:
                continue
            fm = yaml.safe_load(match.group(1)) or {}
            assert "effort" not in fm, (
                f"{rel_path} must not have an effort key (out-of-scope per spec)"
            )
