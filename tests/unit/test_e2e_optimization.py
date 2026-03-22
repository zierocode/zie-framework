import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


# ── Task 1–4: Config collapse ─────────────────────────────────────────────────


class TestConfigCollapseImplement:
    def test_implement_no_config_key_enumeration(self):
        """zie-implement pre-flight must not enumerate config keys as comma-separated list."""
        content = read("commands/zie-implement.md")
        assert "project_type, test_runner" not in content, \
            "zie-implement must not enumerate config keys (project_type, test_runner) — collapse to intent line"


class TestConfigCollapseFix:
    def test_fix_no_config_key_enumeration(self):
        """zie-fix pre-flight must not enumerate config keys."""
        content = read("commands/zie-fix.md")
        assert "project_type, test_runner" not in content, \
            "zie-fix must not enumerate config keys in pre-flight"


class TestConfigCollapseRelease:
    def test_release_no_config_key_enumeration(self):
        """zie-release pre-flight must not enumerate config keys as comma list."""
        content = read("commands/zie-release.md")
        assert "has_frontend, playwright_enabled, test_runner" not in content, \
            "zie-release must not enumerate config keys — collapse to intent line"


class TestConfigCollapseStatus:
    def test_status_no_config_key_enumeration(self):
        """zie-status step 2 must not enumerate config keys as comma list."""
        content = read("commands/zie-status.md")
        assert "project_type, test_runner, has_frontend, playwright_enabled" not in content, \
            "zie-status must not enumerate all config keys — collapse to intent read"


# ── Task 5–6: Pre-flight simplify + handoff blocks ───────────────────────────


class TestHandoffBlockBacklog:
    def test_backlog_has_handoff_block(self):
        content = read("commands/zie-backlog.md")
        assert "## ขั้นตอนถัดไป" in content, \
            "zie-backlog must have a ## ขั้นตอนถัดไป handoff block"

    def test_backlog_handoff_suggests_zie_spec(self):
        content = read("commands/zie-backlog.md")
        handoff_start = content.find("## ขั้นตอนถัดไป")
        assert handoff_start != -1, "zie-backlog must have ## ขั้นตอนถัดไป"
        handoff_section = content[handoff_start:]
        assert "/zie-spec" in handoff_section, \
            "zie-backlog handoff must suggest /zie-spec as next step"

    def test_backlog_preflight_is_concise(self):
        """Pre-flight in zie-backlog must be ≤ 3 items."""
        content = read("commands/zie-backlog.md")
        preflight_start = content.find("## ตรวจสอบก่อนเริ่ม")
        next_section = content.find("\n## ", preflight_start + 1)
        preflight_section = content[preflight_start:next_section]
        # Count numbered items (1. 2. 3.)
        items = [line for line in preflight_section.split("\n")
                 if line.strip() and line.strip()[0].isdigit() and ". " in line]
        assert len(items) <= 3, \
            f"zie-backlog pre-flight must have ≤ 3 items, found {len(items)}"


class TestHandoffBlockPlan:
    def test_plan_has_handoff_block(self):
        content = read("commands/zie-plan.md")
        assert "## ขั้นตอนถัดไป" in content, \
            "zie-plan must have a ## ขั้นตอนถัดไป handoff block"

    def test_plan_handoff_suggests_zie_implement(self):
        content = read("commands/zie-plan.md")
        handoff_start = content.find("## ขั้นตอนถัดไป")
        assert handoff_start != -1, "zie-plan must have ## ขั้นตอนถัดไป"
        handoff_section = content[handoff_start:]
        assert "/zie-implement" in handoff_section, \
            "zie-plan handoff must suggest /zie-implement as next step"


# ── Task 7: Intent-driven RED/GREEN/REFACTOR in zie-implement ─────────────────


class TestIntentDrivenImplement:
    def test_red_section_not_bullet_list(self):
        """RED section in zie-implement must be intent paragraph, not 4+ bullet items."""
        content = read("commands/zie-implement.md")
        red_start = content.find("(RED)")
        green_start = content.find("(GREEN)")
        assert red_start != -1 and green_start != -1, \
            "zie-implement must have (RED) and (GREEN) phase markers"
        red_section = content[red_start:green_start]
        # Count bullet lines (lines starting with "   -")
        bullet_lines = [ln for ln in red_section.split("\n")
                        if ln.strip().startswith("- ")]
        assert len(bullet_lines) <= 2, \
            f"zie-implement RED section must be intent-driven (≤ 2 bullets), found {len(bullet_lines)}"


# ── Task 9: Gate descriptions simplified in zie-release ───────────────────────


class TestGateDescriptionsRelease:
    def test_unit_test_gate_is_concise(self):
        """zie-release unit test gate must be ≤ 3 lines of description."""
        content = read("commands/zie-release.md")
        gate_start = content.find("### ตรวจสอบ: Unit Tests")
        next_gate = content.find("### ตรวจสอบ:", gate_start + 1)
        assert gate_start != -1, "zie-release must have ตรวจสอบ: Unit Tests section"
        gate_section = content[gate_start:next_gate]
        # Count non-empty, non-heading, non-code-fence lines
        desc_lines = [ln for ln in gate_section.split("\n")
                      if ln.strip()
                      and not ln.strip().startswith("#")
                      and not ln.strip().startswith("```")
                      and ln.strip() != "make test-unit"]
        assert len(desc_lines) <= 3, \
            f"zie-release unit gate must be concise (≤ 3 description lines), found {len(desc_lines)}: {desc_lines}"


# ── Task 10: Memory pattern standardization ──────────────────────────────────


class TestMemoryPatternStandardization:
    def test_all_recalls_have_limit_param(self):
        """Every recall call in command files must include a limit= parameter."""
        commands = [
            "commands/zie-implement.md",
            "commands/zie-fix.md",
            "commands/zie-release.md",
            "commands/zie-backlog.md",
            "commands/zie-plan.md",
            "commands/zie-retro.md",
        ]
        for cmd_path in commands:
            content = read(cmd_path)
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "recall " in line and "recall project" in line:
                    assert "limit=" in line, \
                        f"{cmd_path}:{i+1} — recall call missing limit= parameter: {line.strip()!r}"

    def test_implement_wip_remember_uses_supersedes(self):
        """zie-implement WIP checkpoint remember must use supersedes to prevent duplicate WIPs."""
        content = read("commands/zie-implement.md")
        assert "supersedes" in content, \
            "zie-implement WIP remember must use supersedes= to prevent duplicate WIP memories"
