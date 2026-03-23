from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
TEMPLATES = ROOT / "templates"
COMMANDS = ROOT / "commands"


def test_python_template_has_release_skeleton():
    content = (TEMPLATES / "Makefile.python.template").read_text()
    assert "release:" in content
    assert "ZIE-NOT-READY" in content
    assert "@exit 1" in content


def test_typescript_template_has_release_skeleton():
    content = (TEMPLATES / "Makefile.typescript.template").read_text()
    assert "release:" in content
    assert "ZIE-NOT-READY" in content
    assert "@exit 1" in content


def test_zie_release_has_readiness_gate():
    content = (COMMANDS / "zie-release.md").read_text()
    assert "ZIE-NOT-READY" in content
    assert "make release NEW=" in content


def test_zie_release_no_direct_git_ops():
    content = (COMMANDS / "zie-release.md").read_text()
    assert "git merge dev" not in content
    assert "git push origin main" not in content


def test_zie_init_has_release_negotiation():
    content = (COMMANDS / "zie-init.md").read_text()
    assert "make release" in content
    assert "ZIE-NOT-READY" in content
    assert "project_type" in content
