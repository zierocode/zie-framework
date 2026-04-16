import json
from pathlib import Path

RELEASE_CMD = Path(__file__).parents[2] / "commands" / "release.md"
ROOT = Path(__file__).parents[2]


class TestVersioningGate:
    def test_versioning_gate_section_present(self):
        text = RELEASE_CMD.read_text()
        assert "VERSION" in text and ("Verify" in text or "verify" in text or "Version" in text or "version" in text), (
            "zie-release.md must contain a version verification step"
        )

    def test_gate_references_version_file(self):
        text = RELEASE_CMD.read_text()
        assert "VERSION" in text

    def test_gate_references_version_bump(self):
        """VERSION bump step present (plugin.json sync handled by make bump in Makefile)."""
        text = RELEASE_CMD.read_text()
        assert "Bump VERSION" in text or "make bump" in text, "release.md must reference VERSION bumping"

    def test_gate_includes_bump_remediation(self):
        text = RELEASE_CMD.read_text()
        assert "make bump" in text, "zie-release.md must reference 'make bump' as the remediation"

    def test_gate_includes_version_check(self):
        text = RELEASE_CMD.read_text()
        assert "cat VERSION" in text or "VERSION" in text, "zie-release.md must check VERSION file"

    def test_version_files_match(self):
        """VERSION file and plugin.json must contain the same version string."""
        version_file = (ROOT / "VERSION").read_text().strip()
        plugin_json = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        assert version_file == plugin_json["version"], (
            f"VERSION file ({version_file}) does not match "
            f"plugin.json version ({plugin_json['version']}). "
            f"Run 'make bump NEW={version_file}' to sync them."
        )
