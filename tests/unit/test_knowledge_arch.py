import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ZIE = os.path.join(REPO_ROOT, "zie-framework")


def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


class TestProjectMdHub:
    def test_project_md_exists(self):
        assert os.path.isfile(os.path.join(ZIE, "PROJECT.md")), \
            "zie-framework/PROJECT.md must exist"

    def test_project_md_size_limit(self):
        with open(os.path.join(ZIE, "PROJECT.md")) as f:
            lines = f.readlines()
        assert len(lines) <= 80, \
            f"PROJECT.md must be ≤ 80 lines (hub stays lean), found {len(lines)}"

    def test_project_md_has_command_table(self):
        content = read("zie-framework/PROJECT.md")
        assert "## Commands" in content, \
            "PROJECT.md must have a ## Commands section"

    def test_project_md_has_knowledge_links(self):
        content = read("zie-framework/PROJECT.md")
        assert "project/architecture.md" in content
        assert "project/components.md" in content
        assert "project/context.md" in content


class TestSpokes:
    def test_architecture_md_exists(self):
        assert os.path.isfile(os.path.join(ZIE, "project", "architecture.md")), \
            "zie-framework/project/architecture.md must exist"

    def test_components_md_exists(self):
        assert os.path.isfile(os.path.join(ZIE, "project", "components.md")), \
            "zie-framework/project/components.md must exist"

    def test_context_md_exists(self):
        assert os.path.isfile(os.path.join(ZIE, "project", "context.md")), \
            "zie-framework/project/context.md must exist"


class TestInitTemplates:
    def test_project_md_template_exists(self):
        assert os.path.isfile(os.path.join(REPO_ROOT, "templates", "PROJECT.md.template")), \
            "templates/PROJECT.md.template must exist for /init"

    def test_project_template_has_placeholder(self):
        content = read("templates/PROJECT.md.template")
        assert "{{project_name}}" in content, \
            "PROJECT.md.template must use {{project_name}} placeholder"

    def test_project_spoke_templates_exist(self):
        for spoke in ["architecture.md.template", "components.md.template", "context.md.template"]:
            path = os.path.join(REPO_ROOT, "templates", "project", spoke)
            assert os.path.isfile(path), f"templates/project/{spoke} must exist for /init"

    def test_init_references_project_md(self):
        content = read("commands/init.md")
        assert "PROJECT.md" in content, \
            "/init must reference PROJECT.md creation"


class TestRetroKnowledgeSync:
    def test_retro_has_knowledge_sync_section(self):
        content = read("commands/retro.md")
        assert "project/components.md" in content, \
            "/retro must reference project/components.md for knowledge sync"

    def test_retro_has_supersedes_pattern(self):
        content = read("commands/retro.md")
        assert "supersedes" in content, \
            "/retro knowledge sync must use supersedes= to prevent duplicate project snapshots"
