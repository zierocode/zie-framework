"""Tests for model: and effort: frontmatter fields in skills and commands.

Policy: every command and skill must have both model and effort pinned.
Valid model values: haiku | sonnet | opus
Valid effort values: low | medium | high
"""
import re
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

# Complete model+effort map for every command and skill.
# Format: relative_path -> (model, effort)
EXPECTED = {
    # Commands
    "commands/zie-status.md":    ("haiku",  "low"),
    "commands/zie-backlog.md":   ("haiku",  "low"),
    "commands/zie-spec.md":      ("sonnet", "high"),
    "commands/zie-plan.md":      ("sonnet", "high"),
    "commands/zie-implement.md": ("sonnet", "medium"),
    "commands/zie-fix.md":       ("sonnet", "medium"),
    "commands/zie-release.md":   ("sonnet", "medium"),
    "commands/zie-retro.md":     ("sonnet", "high"),
    "commands/zie-init.md":      ("sonnet", "medium"),
    "commands/zie-resync.md":    ("sonnet", "medium"),
    "commands/zie-audit.md":     ("opus",   "high"),
    # Skills
    "skills/spec-design/SKILL.md":   ("sonnet", "high"),
    "skills/write-plan/SKILL.md":    ("sonnet", "high"),
    "skills/debug/SKILL.md":         ("sonnet", "medium"),
    "skills/spec-reviewer/SKILL.md": ("haiku",  "low"),
    "skills/plan-reviewer/SKILL.md": ("haiku",  "low"),
    "skills/impl-reviewer/SKILL.md": ("haiku",  "low"),
    "skills/verify/SKILL.md":        ("haiku",  "low"),
    "skills/tdd-loop/SKILL.md":      ("haiku",  "low"),
    "skills/test-pyramid/SKILL.md":  ("haiku",  "low"),
    "skills/retro-format/SKILL.md":  ("haiku",  "low"),
    "skills/zie-audit/SKILL.md":     ("opus",   "high"),
}

VALID_MODELS = {"haiku", "sonnet", "opus"}
VALID_EFFORTS = {"low", "medium", "high"}


def parse_frontmatter(rel_path: str) -> dict:
    """Extract and parse YAML frontmatter from a markdown file."""
    text = (REPO_ROOT / rel_path).read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"No frontmatter block found in {rel_path}"
    return yaml.safe_load(match.group(1))


class TestAllFilesHaveBothKeys:
    """Every command and skill in EXPECTED must have model and effort."""

    def test_all_have_model_key(self):
        missing = []
        for rel_path in EXPECTED:
            fm = parse_frontmatter(rel_path)
            if "model" not in fm:
                missing.append(rel_path)
        assert missing == [], f"Missing 'model' key in:\n" + "\n".join(missing)

    def test_all_have_effort_key(self):
        missing = []
        for rel_path in EXPECTED:
            fm = parse_frontmatter(rel_path)
            if "effort" not in fm:
                missing.append(rel_path)
        assert missing == [], f"Missing 'effort' key in:\n" + "\n".join(missing)

    def test_all_model_values_are_valid(self):
        errors = []
        for rel_path in EXPECTED:
            fm = parse_frontmatter(rel_path)
            val = fm.get("model")
            if val not in VALID_MODELS:
                errors.append(f"{rel_path}: model={val!r}")
        assert errors == [], "Invalid model values:\n" + "\n".join(errors)

    def test_all_effort_values_are_valid(self):
        errors = []
        for rel_path in EXPECTED:
            fm = parse_frontmatter(rel_path)
            val = fm.get("effort")
            if val not in VALID_EFFORTS:
                errors.append(f"{rel_path}: effort={val!r}")
        assert errors == [], "Invalid effort values:\n" + "\n".join(errors)


class TestExpectedValues:
    """Each file must have the exact model+effort pair defined in EXPECTED."""

    def test_correct_model_values(self):
        errors = []
        for rel_path, (expected_model, _) in EXPECTED.items():
            fm = parse_frontmatter(rel_path)
            actual = fm.get("model")
            if actual != expected_model:
                errors.append(
                    f"{rel_path}: expected model={expected_model!r}, got {actual!r}"
                )
        assert errors == [], "Wrong model values:\n" + "\n".join(errors)

    def test_correct_effort_values(self):
        errors = []
        for rel_path, (_, expected_effort) in EXPECTED.items():
            fm = parse_frontmatter(rel_path)
            actual = fm.get("effort")
            if actual != expected_effort:
                errors.append(
                    f"{rel_path}: expected effort={expected_effort!r}, got {actual!r}"
                )
        assert errors == [], "Wrong effort values:\n" + "\n".join(errors)


class TestOpusFiles:
    """Opus is reserved for the most complex, infrequent tasks."""

    def test_zie_audit_command_is_opus(self):
        fm = parse_frontmatter("commands/zie-audit.md")
        assert fm.get("model") == "opus", "commands/zie-audit.md must use opus"

    def test_zie_audit_skill_is_opus(self):
        fm = parse_frontmatter("skills/zie-audit/SKILL.md")
        assert fm.get("model") == "opus", "skills/zie-audit/SKILL.md must use opus"

    def test_only_audit_files_use_opus(self):
        """No other file should quietly gain an opus pin."""
        opus_files = [
            rel for rel, (model, _) in EXPECTED.items() if model == "opus"
        ]
        assert set(opus_files) == {
            "commands/zie-audit.md",
            "skills/zie-audit/SKILL.md",
        }, f"Unexpected opus files: {opus_files}"


class TestHaikuFiles:
    """Haiku is for mechanical, checklist, and reference tasks."""

    EXPECTED_HAIKU = [
        "commands/zie-status.md",
        "commands/zie-backlog.md",
        "skills/spec-reviewer/SKILL.md",
        "skills/plan-reviewer/SKILL.md",
        "skills/impl-reviewer/SKILL.md",
        "skills/verify/SKILL.md",
        "skills/tdd-loop/SKILL.md",
        "skills/test-pyramid/SKILL.md",
        "skills/retro-format/SKILL.md",
    ]

    def test_haiku_files_have_correct_model(self):
        errors = []
        for rel_path in self.EXPECTED_HAIKU:
            fm = parse_frontmatter(rel_path)
            if fm.get("model") != "haiku":
                errors.append(f"{rel_path}: got model={fm.get('model')!r}")
        assert errors == [], "Wrong model for haiku files:\n" + "\n".join(errors)

    def test_haiku_files_have_low_effort(self):
        errors = []
        for rel_path in self.EXPECTED_HAIKU:
            fm = parse_frontmatter(rel_path)
            if fm.get("effort") != "low":
                errors.append(f"{rel_path}: got effort={fm.get('effort')!r}")
        assert errors == [], "Wrong effort for haiku files:\n" + "\n".join(errors)
