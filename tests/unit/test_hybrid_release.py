"""Tests for the base Makefile template + Makefile.local release architecture."""
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
TEMPLATES = ROOT / "templates"
COMMANDS = ROOT / "commands"


def test_base_makefile_template_exists():
    assert (TEMPLATES / "Makefile").exists(), \
        "templates/Makefile (base template) must exist"


def test_base_makefile_has_release_target():
    content = (TEMPLATES / "Makefile").read_text()
    assert "release:" in content
    assert "ZIE-NOT-READY" not in content, \
        "base template must have a real release target, not ZIE-NOT-READY"


def test_base_makefile_has_bump_extra_hook():
    content = (TEMPLATES / "Makefile").read_text()
    assert "_bump-extra" in content, \
        "base template must define the _bump-extra hook"


def test_base_makefile_has_publish_hook():
    content = (TEMPLATES / "Makefile").read_text()
    assert "_publish" in content, \
        "base template must define the _publish hook"


def test_python_example_local_exists():
    assert (TEMPLATES / "Makefile.local.python.example").exists(), \
        "templates/Makefile.local.python.example must exist"


def test_typescript_example_local_exists():
    assert (TEMPLATES / "Makefile.local.typescript.example").exists(), \
        "templates/Makefile.local.typescript.example must exist"


def test_python_example_has_bump_extra():
    content = (TEMPLATES / "Makefile.local.python.example").read_text()
    assert "_bump-extra" in content


def test_typescript_example_has_bump_extra():
    content = (TEMPLATES / "Makefile.local.typescript.example").read_text()
    assert "_bump-extra" in content


def test_zie_release_no_zie_not_ready():
    content = (COMMANDS / "release.md").read_text()
    assert "ZIE-NOT-READY" not in content, \
        "zie-release.md must not contain ZIE-NOT-READY (obsolete gate)"


def test_zie_release_does_not_call_make_release():
    """v1.28.4: /release skill does git ops directly to avoid duplication."""
    content = (COMMANDS / "release.md").read_text()
    assert "make release NEW=" not in content, \
        "/release must NOT call 'make release' (duplicates git ops)"


def test_zie_release_does_git_ops_directly():
    """v1.28.4: /release skill performs git ops directly."""
    content = (COMMANDS / "release.md").read_text()
    assert "git merge dev" in content, \
        "/release must merge dev → main directly"
    assert "git push origin main" in content, \
        "/release must push main directly"
    assert "git tag -s" in content, \
        "/release must create tag directly"


def test_zie_init_has_makefile_local_creation():
    content = (COMMANDS / "init.md").read_text()
    assert "Makefile.local" in content, \
        "zie-init.md must reference Makefile.local creation"


def test_zie_init_has_bump_extra_negotiation():
    content = (COMMANDS / "init.md").read_text()
    assert "_bump-extra" in content, \
        "zie-init.md must negotiate _bump-extra in step 7"


def test_zie_init_no_zie_not_ready():
    content = (COMMANDS / "init.md").read_text()
    assert "ZIE-NOT-READY" not in content, \
        "zie-init.md must not reference ZIE-NOT-READY (obsolete pattern)"


class TestReleaseLeanFallbackExtension:
    def test_zie_release_no_blocking_docs_sync_fallback(self):
        """Release must not block on docs-sync-check when Agent unavailable."""
        content = (COMMANDS / "release.md").read_text()
        assert "call Skill(zie-framework:docs-sync-check) inline" not in content, (
            "Blocking inline Skill fallback must be replaced with graceful skip message"
        )
