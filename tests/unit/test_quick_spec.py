from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
COMMANDS = ROOT / "commands"


def read_cmd(name):
    return (COMMANDS / f"zie-{name}.md").read_text()


def test_quick_spec_mode_detection_spaces():
    content = read_cmd("spec")
    assert "contains spaces" in content or "spaces" in content


def test_quick_spec_mode_detection_no_backlog():
    content = read_cmd("spec")
    assert "No backlog file" in content or "no backlog file" in content


def test_quick_spec_prints_mode_message():
    content = read_cmd("spec")
    assert "Quick spec mode" in content


def test_quick_spec_passes_idea_to_spec_design():
    content = read_cmd("spec")
    assert "spec-design" in content
    assert "inline idea" in content or "idea string" in content


def test_quick_spec_slug_derivation():
    content = read_cmd("spec")
    assert "kebab-case" in content or "kebab" in content


def test_quick_spec_roadmap_update():
    content = read_cmd("spec")
    assert "ROADMAP" in content


def test_existing_slug_flow_preserved():
    content = read_cmd("spec")
    assert "backlog/" in content
