"""Tests for Feature D — Docs + Standards Sprint"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


class TestPluginJsonVersion:
    def test_plugin_json_version_matches_version_file(self):
        plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
        version = (REPO_ROOT / "VERSION").read_text().strip()
        assert plugin["version"] == version, (
            f"plugin.json version '{plugin['version']}' != VERSION '{version}'"
        )

    def test_makefile_has_sync_version_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text()
        assert "sync-version:" in makefile


class TestPreCommitHook:
    def test_githooks_pre_commit_exists(self):
        assert (REPO_ROOT / ".githooks" / "pre-commit").exists()

    def test_pre_commit_contains_sync_version(self):
        content = (REPO_ROOT / ".githooks" / "pre-commit").read_text()
        assert "sync-version" in content

    def test_makefile_wires_core_hooks_path(self):
        makefile = (REPO_ROOT / "Makefile").read_text()
        assert "core.hooksPath" in makefile and ".githooks" in makefile


class TestReadmeReferences:
    def test_no_decisions_md_in_readme(self):
        readme = (REPO_ROOT / "README.md").read_text()
        lines_with_decisions = [
            line for line in readme.splitlines() if "decisions.md" in line
        ]
        assert lines_with_decisions == [], (
            f"Found 'decisions.md' in README.md: {lines_with_decisions}"
        )

    def test_context_md_referenced_in_readme(self):
        readme = (REPO_ROOT / "README.md").read_text()
        # project/context.md shown in directory tree under project/ subtree
        assert "project/" in readme and "context.md" in readme


class TestArchitectureMd:
    def test_last_updated_is_2026_03_23(self):
        arch = (REPO_ROOT / "zie-framework" / "project" / "architecture.md").read_text()
        assert "2026-03-23" in arch

    def test_v1_3_0_in_architecture(self):
        arch = (REPO_ROOT / "zie-framework" / "project" / "architecture.md").read_text()
        assert "v1.3.0" in arch

    def test_v1_4_0_in_architecture(self):
        arch = (REPO_ROOT / "zie-framework" / "project" / "architecture.md").read_text()
        assert "v1.4.0" in arch


class TestContextMdAdrNumbering:
    def test_no_d_prefix_headers_remain(self):
        context = (REPO_ROOT / "zie-framework" / "project" / "context.md").read_text()
        bad_lines = [
            line for line in context.splitlines()
            if re.match(r'^## D-\d+', line)
        ]
        assert bad_lines == [], f"Found D- prefixed headers: {bad_lines}"

    def test_adr_prefix_headers_present(self):
        context = (REPO_ROOT / "zie-framework" / "project" / "context.md").read_text()
        adr_headers = [
            line for line in context.splitlines()
            if re.match(r'^## ADR-\d+', line)
        ]
        assert len(adr_headers) >= 9, (
            f"Expected at least 9 ADR-NNN headers, found {len(adr_headers)}: {adr_headers}"
        )


class TestChangelogTranslation:
    def test_v1_1_0_section_has_no_thai_script(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        # Extract v1.1.0 section
        lines = changelog.splitlines()
        in_section = False
        section_lines = []
        for line in lines:
            if line.strip() == "## v1.1.0 — 2026-03-22":
                in_section = True
                continue
            if in_section and line.startswith("## v"):
                break
            if in_section:
                section_lines.append(line)
        assert section_lines, "v1.1.0 section not found"
        section_text = "\n".join(section_lines)
        thai_chars = [c for c in section_text if 0x0E00 < ord(c) < 0x0E80]
        assert thai_chars == [], (
            f"Thai characters found in v1.1.0 section: {''.join(thai_chars[:20])}"
        )


class TestSecurityMd:
    def test_security_md_exists(self):
        assert (REPO_ROOT / "SECURITY.md").exists()

    def test_security_md_has_reporting_method(self):
        content = (REPO_ROOT / "SECURITY.md").read_text()
        assert "report" in content.lower() or "Report" in content

    def test_security_md_has_maintainer_contact(self):
        content = (REPO_ROOT / "SECURITY.md").read_text()
        assert any(w in content for w in ["contact", "Contact", "maintainer"])

    def test_security_md_has_disclosure_policy(self):
        content = (REPO_ROOT / "SECURITY.md").read_text()
        assert any(w in content for w in ["90", "embargo", "responsible disclosure"])


class TestCzToml:
    def test_cz_toml_exists(self):
        assert (REPO_ROOT / ".cz.toml").exists()

    def test_cz_toml_has_tool_commitizen(self):
        content = (REPO_ROOT / ".cz.toml").read_text()
        assert "[tool.commitizen]" in content

    def test_cz_toml_has_conventional_commits(self):
        content = (REPO_ROOT / ".cz.toml").read_text()
        assert "conventional_commits" in content

    def test_cz_toml_has_required_commit_types(self):
        content = (REPO_ROOT / ".cz.toml").read_text()
        for t in ("feat", "fix", "chore"):
            assert t in content, f"commit type '{t}' missing from .cz.toml"
