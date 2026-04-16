"""Tests for workflow-lean: --focus flag, --draft-plan flag, spec-design args, zie-init section loop."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


class TestZieAuditFocusFlag:
    """Focus flag logic lives in the audit skill (canonical since lean-dual-audit-pipeline)."""

    def test_focus_flag_documented(self):
        # audit.md (thin dispatcher) documents --focus; skill handles it
        text = read("commands/audit.md")
        assert "--focus" in text, "audit.md must document --focus flag"

    def test_focus_map_present(self):
        text = read("skills/audit/SKILL.md")
        assert "focus" in text.lower() or "Focus map" in text, "audit skill must have focus map for agent selection"

    def test_all_four_focus_tokens_listed(self):
        text = read("skills/audit/SKILL.md")
        for token in ["security", "code", "structure", "external"]:
            assert token in text, f"audit skill focus map must include '{token}'"

    def test_unrecognized_focus_runs_all(self):
        text = read("skills/audit/SKILL.md")
        assert "full audit" in text.lower() or "all agents" in text.lower() or "unrecognized" in text.lower(), (
            "audit skill must run all agents for unrecognized focus value"
        )

    def test_conditional_agent_spawn(self):
        text = read("skills/audit/SKILL.md")
        assert "active_agents" in text or "conditional" in text.lower(), (
            "audit skill must conditionally spawn agents based on focus"
        )


class TestZieSpecDraftPlanFlag:
    def test_draft_plan_flag_documented(self):
        text = read("commands/spec.md")
        assert "--draft-plan" in text, "zie-spec must document --draft-plan flag"

    def test_draft_plan_invokes_write_plan(self):
        text = read("commands/spec.md")
        assert "write-plan" in text, "zie-spec --draft-plan must invoke write-plan skill"

    def test_no_flag_normal_handoff(self):
        text = read("commands/spec.md")
        assert "/plan" in text and "Next:" in text, "zie-spec without --draft-plan must print normal handoff"

    def test_flag_removed_from_slug_extraction(self):
        text = read("commands/spec.md")
        assert "clean_args" in text or "remove" in text.lower() or '!= "--draft-plan"' in text, (
            "zie-spec must strip --draft-plan flag from slug extraction"
        )


class TestSpecDesignArgsTable:
    def test_three_argument_rows(self):
        text = read("skills/spec-design/SKILL.md")
        assert "$ARGUMENTS[2]" in text, "spec-design Arguments table must document position 2"

    def test_draft_plan_documented(self):
        text = read("skills/spec-design/SKILL.md")
        assert "--draft-plan" in text, "spec-design Arguments table must reference --draft-plan"

    def test_control_plane_note(self):
        text = read("skills/spec-design/SKILL.md")
        assert "control plane" in text.lower() or "ADR-003" in text, (
            "spec-design must note --draft-plan is handled by control plane"
        )


class TestZieInitSectionLoop:
    def test_section_targeted_prompt_present(self):
        text = read("commands/init.md")
        assert "which section to revise" in text.lower() or "Which section" in text, (
            "zie-init must ask which section to revise"
        )

    def test_section_options_documented(self):
        text = read("commands/init.md")
        for section in ["project", "architecture", "components", "context"]:
            assert section in text, f"zie-init revision options must include '{section}'"

    def test_all_good_exits_loop(self):
        text = read("commands/init.md")
        assert "all good" in text.lower(), "zie-init must accept 'all good' to exit revision loop"

    def test_other_sections_retain_state(self):
        text = read("commands/init.md")
        assert "retain" in text.lower() or "other" in text.lower() or "prior state" in text.lower(), (
            "zie-init revision loop must retain other sections' draft state"
        )
