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

    def test_write_plan_has_memory_recall(self):
        content = read("skills/write-plan/SKILL.md")
        assert "recall" in content or "zie_memory_enabled" in content, \
            "write-plan skill must include zie-memory recall integration"

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
    def test_zie_spec_no_superpowers_skill(self):
        content = read("commands/zie-spec.md")
        assert "Skill(superpowers:" not in content, \
            "zie-spec must not call Skill(superpowers:*) after fork"

    def test_zie_implement_no_superpowers_skill(self):
        content = read("commands/zie-implement.md")
        assert "Skill(superpowers:" not in content, \
            "zie-implement must not call Skill(superpowers:*) after fork"

    def test_zie_fix_no_superpowers_skill(self):
        content = read("commands/zie-fix.md")
        assert "Skill(superpowers:" not in content, \
            "zie-fix must not call Skill(superpowers:*) after fork"

    def test_zie_release_no_superpowers_skill(self):
        content = read("commands/zie-release.md")
        assert "Skill(superpowers:" not in content, \
            "zie-release must not call Skill(superpowers:*) after fork"

    def test_zie_spec_calls_zie_framework_spec_design(self):
        content = read("commands/zie-spec.md")
        assert "Skill(zie-framework:spec-design)" in content, \
            "zie-spec must invoke Skill(zie-framework:spec-design)"

    def test_spec_design_does_not_auto_invoke_write_plan(self):
        # spec-design must NOT auto-invoke write-plan — commands are the control
        # plane; zie-plan handles the write-plan handoff after spec approval.
        content = read("skills/spec-design/SKILL.md")
        assert "Skill(zie-framework:write-plan)" not in content, \
            "spec-design must not auto-invoke write-plan (pipeline divergence fix)"
        assert "/zie-plan" in content, \
            "spec-design must print handoff to /zie-plan instead of invoking write-plan"

    def test_zie_implement_calls_zie_framework_tdd_loop(self):
        content = read("commands/zie-implement.md")
        assert "Skill(zie-framework:tdd-loop)" in content, \
            "zie-implement must invoke Skill(zie-framework:tdd-loop)"

    def test_zie_implement_calls_zie_framework_debug(self):
        content = read("commands/zie-implement.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-implement must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_debug(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-fix must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_verify(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:verify)" in content, \
            "zie-fix must invoke Skill(zie-framework:verify)"

    def test_zie_release_has_todo_and_secrets_check(self):
        content = read("commands/zie-release.md")
        assert "TODO" in content, \
            "zie-release must include inline TODO scan (verify skill removed — tests covered by Gates 1-3)"
        assert "secrets" in content.lower() or "credentials" in content.lower(), \
            "zie-release must include secrets check"

    def test_zie_plan_no_superpowers_enabled(self):
        content = read("commands/zie-plan.md")
        assert "superpowers_enabled" not in content, \
            "zie-plan must not read superpowers_enabled from .config"

    def test_zie_init_no_superpowers_enabled_in_config_template(self):
        content = read("commands/zie-init.md")
        assert "superpowers_enabled" not in content, \
            "zie-init .config template must not include superpowers_enabled field"

    def test_session_resume_no_superpowers_enabled(self):
        content = read("hooks/session-resume.py")
        assert "superpowers_enabled" not in content, \
            "session-resume hook must not read superpowers_enabled from config"
