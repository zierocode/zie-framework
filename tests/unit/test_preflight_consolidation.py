from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"

REFERENCE_LINE = "command-conventions.md#pre-flight"


def _preflight_body(cmd: str) -> str:
    text = (COMMANDS_DIR / f"{cmd}.md").read_text()
    start = text.find("## ตรวจสอบก่อนเริ่ม")
    assert start != -1, f"{cmd}.md must have ## ตรวจสอบก่อนเริ่ม"
    end = text.find("\n## ", start + 1)
    return text[start:end] if end != -1 else text[start:]


# T2: spec.md, plan.md, resync.md


def test_spec_preflight_is_reference():
    body = _preflight_body("spec")
    assert REFERENCE_LINE in body, "spec.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


def test_plan_preflight_is_reference():
    body = _preflight_body("plan")
    assert REFERENCE_LINE in body, "plan.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


def test_resync_preflight_is_reference():
    body = _preflight_body("resync")
    assert REFERENCE_LINE in body, "resync.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


# T3: fix.md, backlog.md


def test_fix_preflight_is_reference():
    body = _preflight_body("fix")
    assert REFERENCE_LINE in body, "fix.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


def test_backlog_preflight_is_reference():
    body = _preflight_body("backlog")
    assert REFERENCE_LINE in body, "backlog.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


# T4: implement.md


def test_implement_preflight_is_reference():
    body = _preflight_body("implement")
    assert REFERENCE_LINE in body, "implement.md pre-flight must reference command-conventions.md#pre-flight"
    assert "Check `zie-framework/` exists" not in body


def test_implement_retains_live_context():
    body = _preflight_body("implement")
    assert "git log" in body, "implement.md must retain live git log bash injection"
    assert "git status" in body


def test_implement_retains_agent_advisory():
    body = _preflight_body("implement")
    assert "agent" in body.lower() or "builder" in body


def test_implement_retains_ready_guard():
    body = _preflight_body("implement")
    assert "Ready" in body
