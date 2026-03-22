import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def skill_path(name):
    return os.path.join(REPO_ROOT, "skills", name, "SKILL.md")


def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


class TestSkillFilesExist:
    def test_spec_design_skill_exists(self):
        assert os.path.exists(skill_path("spec-design")), \
            "skills/spec-design/SKILL.md must exist"

    def test_write_plan_skill_exists(self):
        assert os.path.exists(skill_path("write-plan")), \
            "skills/write-plan/SKILL.md must exist"

    def test_debug_skill_exists(self):
        assert os.path.exists(skill_path("debug")), \
            "skills/debug/SKILL.md must exist"

    def test_verify_skill_exists(self):
        assert os.path.exists(skill_path("verify")), \
            "skills/verify/SKILL.md must exist"


class TestSkillZieMemoryIntegration:
    def test_spec_design_has_zie_memory_recall(self):
        content = read("skills/spec-design/SKILL.md")
        assert "recall" in content and "zie_memory_enabled" in content, \
            "spec-design skill must include zie-memory batch recall instructions"

    def test_spec_design_saves_to_zie_framework_specs(self):
        content = read("skills/spec-design/SKILL.md")
        assert "zie-framework/specs/" in content, \
            "spec-design skill must save specs to zie-framework/specs/"
        assert "docs/superpowers/specs/" not in content, \
            "spec-design skill must not reference superpowers spec path"

    def test_write_plan_saves_to_zie_framework_plans(self):
        content = read("skills/write-plan/SKILL.md")
        assert "zie-framework/plans/" in content, \
            "write-plan skill must save plans to zie-framework/plans/"
        assert "docs/superpowers/plans/" not in content, \
            "write-plan skill must not reference superpowers plan path"

    def test_write_plan_has_context_from_brain_section(self):
        content = read("skills/write-plan/SKILL.md")
        assert "Context from brain" in content, \
            "write-plan skill must include ## Context from brain section in plan template"

    def test_write_plan_has_depends_on_docs(self):
        content = read("skills/write-plan/SKILL.md")
        assert "depends_on" in content, \
            "write-plan skill must document depends_on task marker syntax"

    def test_debug_has_zie_memory_recall(self):
        content = read("skills/debug/SKILL.md")
        assert "recall" in content and "zie_memory_enabled" in content, \
            "debug skill must include zie-memory recall instructions"

    def test_debug_no_superpowers_refs(self):
        content = read("skills/debug/SKILL.md")
        assert "superpowers:" not in content, \
            "debug skill must not reference superpowers: skill names"

    def test_spec_design_no_superpowers_refs(self):
        content = read("skills/spec-design/SKILL.md")
        assert "superpowers:" not in content, \
            "spec-design skill must not reference superpowers: skill names"

    def test_write_plan_no_superpowers_refs(self):
        content = read("skills/write-plan/SKILL.md")
        assert "superpowers:" not in content, \
            "write-plan skill must not reference superpowers: skill names"


class TestCommandsNoSuperpowersDependency:
    def test_zie_idea_no_superpowers_skill(self):
        content = read("commands/zie-idea.md")
        assert "Skill(superpowers:" not in content, \
            "zie-idea must not call Skill(superpowers:*) after fork"

    def test_zie_build_no_superpowers_skill(self):
        content = read("commands/zie-build.md")
        assert "Skill(superpowers:" not in content, \
            "zie-build must not call Skill(superpowers:*) after fork"

    def test_zie_fix_no_superpowers_skill(self):
        content = read("commands/zie-fix.md")
        assert "Skill(superpowers:" not in content, \
            "zie-fix must not call Skill(superpowers:*) after fork"

    def test_zie_ship_no_superpowers_skill(self):
        content = read("commands/zie-ship.md")
        assert "Skill(superpowers:" not in content, \
            "zie-ship must not call Skill(superpowers:*) after fork"

    def test_zie_idea_calls_zie_framework_spec_design(self):
        content = read("commands/zie-idea.md")
        assert "Skill(zie-framework:spec-design)" in content, \
            "zie-idea must invoke Skill(zie-framework:spec-design)"

    def test_zie_idea_calls_zie_framework_write_plan(self):
        content = read("commands/zie-idea.md")
        assert "Skill(zie-framework:write-plan)" in content, \
            "zie-idea must invoke Skill(zie-framework:write-plan)"

    def test_zie_build_calls_zie_framework_tdd_loop(self):
        content = read("commands/zie-build.md")
        assert "Skill(zie-framework:tdd-loop)" in content, \
            "zie-build must invoke Skill(zie-framework:tdd-loop)"

    def test_zie_build_calls_zie_framework_debug(self):
        content = read("commands/zie-build.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-build must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_debug(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-fix must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_verify(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:verify)" in content, \
            "zie-fix must invoke Skill(zie-framework:verify)"

    def test_zie_ship_calls_zie_framework_verify(self):
        content = read("commands/zie-ship.md")
        assert "Skill(zie-framework:verify)" in content, \
            "zie-ship must invoke Skill(zie-framework:verify)"
