import os

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


def cmd(name):
    return os.path.join(REPO_ROOT, "commands", f"{name}.md")


def skill(name):
    return os.path.join(REPO_ROOT, "skills", name, "SKILL.md")


def read(rel):
    with open(os.path.join(REPO_ROOT, rel)) as f:
        return f.read()


class TestNewCommandsExist:
    def test_zie_backlog_exists(self):
        assert os.path.exists(cmd("backlog")), \
            "commands/backlog.md must exist"

    def test_zie_spec_exists(self):
        assert os.path.exists(cmd("spec")), \
            "commands/spec.md must exist"

    def test_zie_implement_exists(self):
        assert os.path.exists(cmd("implement")), \
            "commands/implement.md must exist"

    def test_zie_release_exists(self):
        assert os.path.exists(cmd("release")), \
            "commands/release.md must exist"


class TestOldCommandsRemoved:
    def test_zie_idea_removed(self):
        assert not os.path.exists(cmd("idea")), \
            "commands/idea.md must be removed (split into backlog+spec)"

    def test_zie_build_removed(self):
        assert not os.path.exists(cmd("build")), \
            "commands/build.md must be removed (renamed to implement)"

    def test_zie_ship_removed(self):
        assert not os.path.exists(cmd("ship")), \
            "commands/ship.md must be removed (renamed to release)"


class TestIntentDetectUpdated:
    def _hook(self):
        return read("hooks/intent-sdlc.py")

    def test_has_backlog_suggestion(self):
        assert '"/backlog"' in self._hook(), \
            "intent-detect must suggest /backlog"

    def test_has_spec_suggestion(self):
        assert '"/spec"' in self._hook(), \
            "intent-detect must suggest /spec"

    def test_has_implement_suggestion(self):
        assert '"/implement"' in self._hook(), \
            "intent-detect must suggest /implement"

    def test_has_release_suggestion(self):
        assert '"/release"' in self._hook(), \
            "intent-detect must suggest /release"

    def test_no_idea_suggestion(self):
        assert '"/idea"' not in self._hook(), \
            "intent-detect must not suggest /idea"

    def test_no_build_suggestion(self):
        assert '"/build"' not in self._hook(), \
            "intent-detect must not suggest /build"

    def test_no_ship_suggestion(self):
        assert '"/ship"' not in self._hook(), \
            "intent-detect must not suggest /ship"


class TestReviewerSkillsExist:
    def test_spec_reviewer_exists(self):
        assert os.path.exists(skill("spec-review")), \
            "skills/spec-review/SKILL.md must exist"

    def test_plan_reviewer_exists(self):
        assert os.path.exists(skill("plan-review")), \
            "skills/plan-review/SKILL.md must exist"

    def test_impl_reviewer_exists(self):
        assert os.path.exists(skill("impl-review")), \
            "skills/impl-review/SKILL.md must exist"



class TestSkillsInvokeReviewers:
    def test_spec_design_invokes_spec_reviewer(self):
        content = read("skills/spec-design/SKILL.md")
        assert "spec-review" in content, \
            "spec-design skill must invoke spec-review loop"

    def test_write_plan_invokes_plan_reviewer(self):
        # Reviewer gate lives in zie-plan.md, NOT inside the skill
        skill_content = read("skills/write-plan/SKILL.md")
        assert "plan-review" not in skill_content, \
            "write-plan skill must NOT invoke plan-review (reviewer gate belongs in plan.md)"
        command_content = read("commands/plan.md")
        assert "plan-review" in command_content, \
            "plan.md must contain the plan-review gate"

    def test_implement_invokes_impl_reviewer(self):
        content = read("commands/implement.md")
        assert "impl-review" in content, \
            "implement must invoke impl-review after each task"
