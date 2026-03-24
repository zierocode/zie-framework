import json
from pathlib import Path

RELEASE_CMD = Path(__file__).parents[2] / "commands" / "zie-release.md"
ROOT = Path(__file__).parents[2]


class TestVersioningGate:
    def test_versioning_gate_section_present(self):
        text = RELEASE_CMD.read_text()
        assert "Version Consistency" in text or "version consistency" in text, \
            "zie-release.md must contain a version consistency gate section"

    def test_gate_references_version_file(self):
        text = RELEASE_CMD.read_text()
        assert "VERSION" in text

    def test_gate_references_plugin_json(self):
        text = RELEASE_CMD.read_text()
        assert "plugin.json" in text

    def test_gate_includes_bump_remediation(self):
        text = RELEASE_CMD.read_text()
        assert "make bump" in text, \
            "zie-release.md version gate must reference 'make bump' as the remediation"

    def test_gate_includes_mismatch_message(self):
        text = RELEASE_CMD.read_text()
        assert "mismatch" in text.lower() or "diverge" in text.lower() or \
            "not match" in text.lower() or "do not match" in text.lower(), \
            "zie-release.md version gate must describe a mismatch failure condition"

    def test_version_files_match(self):
        """VERSION file and plugin.json must contain the same version string."""
        version_file = (ROOT / "VERSION").read_text().strip()
        plugin_json = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        assert version_file == plugin_json["version"], (
            f"VERSION file ({version_file}) does not match "
            f"plugin.json version ({plugin_json['version']}). "
            f"Run 'make bump NEW={version_file}' to sync them."
        )
