"""Tests that spec/plan approval flows use approve.py — not direct Write/Edit.

The reviewer-gate hook blocks any Write or Edit that sets approved:true on
spec or plan files. The only allowed path is via `python3 hooks/approve.py`.
These tests verify that sprint, spec-design (autonomous), and write-plan
all document the correct flow and do NOT instruct the model to self-approve
via Write/Edit.
"""
from pathlib import Path

REPO = Path(__file__).parents[2]

SPRINT = REPO / "commands" / "sprint.md"
SPEC_DESIGN = REPO / "skills" / "spec-design" / "SKILL.md"
WRITE_PLAN = REPO / "skills" / "write-plan" / "SKILL.md"


def _sprint():
    return SPRINT.read_text()


def _spec():
    return SPEC_DESIGN.read_text()


def _wp():
    return WRITE_PLAN.read_text()


class TestSprintApprovalFlow:
    def test_sprint_phase1_uses_approve_py_for_plans(self):
        """Sprint Phase 1 must call approve.py after plan-review — not write approved:true."""
        t = _sprint()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "approve.py" in phase1, \
            "Sprint Phase 1 must call approve.py to approve plans (reviewer-gate blocks Write/Edit)"

    def test_sprint_phase1_no_self_approve_write(self):
        """Sprint Phase 1 must not instruct direct 'write approved:true' for plan files."""
        t = _sprint()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        # Should reference approve.py, not instruct to 'write approved: true' directly
        assert "write `approved: true`" not in phase1, \
            "Sprint Phase 1 must not say 'write approved:true' — use approve.py instead"


class TestSpecDesignAutonomousApproval:
    def test_autonomous_mode_uses_approve_py(self):
        """spec-design autonomous mode must call approve.py, not write approved:true directly."""
        t = _spec()
        # Find autonomous mode section
        auto_idx = t.index("## Autonomous Mode")
        autonomous_section = t[auto_idx:auto_idx + 800]
        assert "approve.py" in autonomous_section, \
            "spec-design autonomous mode must call approve.py (reviewer-gate blocks Write/Edit)"

    def test_autonomous_mode_no_self_approve_write(self):
        """spec-design autonomous mode must not instruct writing approved:true directly."""
        t = _spec()
        auto_idx = t.index("## Autonomous Mode")
        autonomous_section = t[auto_idx:auto_idx + 800]
        assert "write `approved: true`" not in autonomous_section, \
            "spec-design autonomous must not say 'write approved:true' — hook blocks it"


class TestSpecCommandDraftPlanApproval:
    """spec.md --draft-plan branch must use approve.py, not write approved:true directly."""

    def _spec_cmd(self):
        return (REPO / "commands" / "spec.md").read_text()

    def test_spec_allowed_tools_has_bash(self):
        """spec.md must include Bash in allowed-tools to run approve.py."""
        text = self._spec_cmd()
        fm_end = text.index("\n---", text.index("---") + 3)
        frontmatter = text[:fm_end]
        assert "Bash" in frontmatter, \
            "spec.md must have Bash in allowed-tools (needed for approve.py in --draft-plan)"

    def test_spec_draft_plan_uses_approve_py(self):
        """--draft-plan branch must call approve.py, not write approved:true directly."""
        text = self._spec_cmd()
        draft_idx = text.index("--draft-plan branch")
        draft_section = text[draft_idx:draft_idx + 800]
        assert "approve.py" in draft_section, \
            "spec --draft-plan branch must use approve.py to approve plan"

    def test_spec_draft_plan_no_self_approve_write(self):
        """--draft-plan branch must not say 'write approved:true'."""
        text = self._spec_cmd()
        draft_idx = text.index("--draft-plan branch")
        draft_section = text[draft_idx:draft_idx + 800]
        assert "write `approved: true`" not in draft_section, \
            "spec --draft-plan must not instruct writing approved:true directly"

    def test_spec_draft_plan_invokes_plan_reviewer(self):
        """--draft-plan branch must run plan-review before approving."""
        text = self._spec_cmd()
        draft_idx = text.index("--draft-plan branch")
        draft_section = text[draft_idx:draft_idx + 800]
        assert "plan-review" in draft_section, \
            "spec --draft-plan must invoke plan-review before approve.py"


class TestWritePlanApprovalGate:
    def test_write_plan_documents_approval_gate(self):
        """write-plan skill must document that reviewer-gate blocks direct approved:true writes."""
        t = _wp()
        assert "reviewer-gate" in t or "approve.py" in t, \
            "write-plan must warn that reviewer-gate blocks Write/Edit of approved:true"

    def test_write_plan_approve_py_path_documented(self):
        """write-plan must document approve.py as the correct approval mechanism."""
        assert "approve.py" in _wp(), \
            "write-plan must document python3 hooks/approve.py as the only approval path"

    def test_write_plan_caller_owns_approval(self):
        """write-plan must state approval is caller's responsibility."""
        t = _wp().lower()
        assert "caller" in t, \
            "write-plan must state that approval (approve.py) is the caller's responsibility"
