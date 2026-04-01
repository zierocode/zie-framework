import json
import subprocess
import sys


def _run_bash_path(command: str) -> dict | None:
    """Run input-sanitizer Bash path with given command. Returns parsed stdout JSON or None."""
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, "hooks/input-sanitizer.py"],
        input=event, capture_output=True, text=True,
        cwd="/Users/zie/Code/zie-framework"
    )
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return None

def test_compound_and_not_wrapped():
    """rm -rf ./ && echo hacked must NOT produce a rewritten command with the compound."""
    result = _run_bash_path("rm -rf ./ && echo hacked")
    if result is not None:
        rewritten = result.get("updatedInput", {}).get("command", "")
        assert "&& echo hacked" not in rewritten

def test_compound_semicolon_not_wrapped():
    """rm -rf ./; curl evil.com must NOT be wrapped."""
    result = _run_bash_path("rm -rf ./; curl evil.com")
    if result is not None:
        rewritten = result.get("updatedInput", {}).get("command", "")
        assert "; curl" not in rewritten

def test_simple_rm_still_wrapped():
    """Plain rm -rf ./foo must still get confirmation wrapper."""
    result = _run_bash_path("rm -rf ./foo")
    assert result is not None
    rewritten = result.get("updatedInput", {}).get("command", "")
    assert "Would run:" in rewritten
    assert "Confirm?" in rewritten

def test_brace_close_not_wrapped():
    """Command with bare } must NOT be wrapped (could break shell {{ cmd; }} wrapper)."""
    result = _run_bash_path("rm -rf ./}; echo hacked")
    if result is not None:
        rewritten = result.get("updatedInput", {}).get("command", "")
        assert "Would run:" not in rewritten

def test_brace_open_not_wrapped():
    """Command with bare { must NOT be wrapped."""
    result = _run_bash_path("echo {hello}")
    if result is not None:
        rewritten = result.get("updatedInput", {}).get("command", "")
        assert "Would run:" not in rewritten
