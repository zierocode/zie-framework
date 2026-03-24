"""Tests for hooks/sdlc-permissions.py"""
import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(command, tool_name="Bash"):
    hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )


def run_hook_raw(stdin_text):
    """Pass arbitrary stdin bytes — used for malformed-JSON test."""
    hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
    return subprocess.run(
        [sys.executable, hook],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def assert_approved(r):
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["decision"]["behavior"] == "allow"


def assert_passthrough(r):
    assert r.returncode == 0
    assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Allowlist — commands that MUST be auto-approved
# ---------------------------------------------------------------------------

class TestAllowlistApproved:
    def test_git_add_dot_approved(self):
        assert_approved(run_hook("git add ."))

    def test_git_add_file_approved(self):
        assert_approved(run_hook("git add hooks/sdlc-permissions.py"))

    def test_git_add_patch_approved(self):
        assert_approved(run_hook("git add -p"))

    def test_git_commit_message_approved(self):
        assert_approved(run_hook('git commit -m "feat: add sdlc permissions hook"'))

    def test_git_commit_amend_no_edit_approved(self):
        assert_approved(run_hook("git commit --amend --no-edit"))

    def test_git_diff_approved(self):
        assert_approved(run_hook("git diff"))

    def test_git_diff_head_approved(self):
        assert_approved(run_hook("git diff HEAD"))

    def test_git_diff_staged_approved(self):
        assert_approved(run_hook("git diff --staged"))

    def test_git_status_approved(self):
        assert_approved(run_hook("git status"))

    def test_git_status_short_approved(self):
        assert_approved(run_hook("git status --short"))

    def test_git_log_approved(self):
        assert_approved(run_hook("git log"))

    def test_git_log_oneline_approved(self):
        assert_approved(run_hook("git log --oneline"))

    def test_git_stash_approved(self):
        assert_approved(run_hook("git stash"))

    def test_git_stash_pop_approved(self):
        assert_approved(run_hook("git stash pop"))

    def test_git_stash_list_approved(self):
        assert_approved(run_hook("git stash list"))

    def test_make_test_approved(self):
        assert_approved(run_hook("make test"))

    def test_make_test_unit_approved(self):
        assert_approved(run_hook("make test-unit"))

    def test_make_test_integration_approved(self):
        assert_approved(run_hook("make test-integration"))

    def test_make_lint_approved(self):
        assert_approved(run_hook("make lint"))

    def test_make_lint_fix_approved(self):
        assert_approved(run_hook("make lint-fix"))

    def test_pytest_approved(self):
        assert_approved(run_hook("python3 -m pytest"))

    def test_pytest_verbose_approved(self):
        assert_approved(run_hook("python3 -m pytest -v"))

    def test_pytest_path_approved(self):
        assert_approved(run_hook("python3 -m pytest tests/"))

    def test_bandit_approved(self):
        assert_approved(run_hook("python3 -m bandit -r ."))


# ---------------------------------------------------------------------------
# Commands explicitly NOT in the allowlist — must pass through (empty stdout)
# ---------------------------------------------------------------------------

class TestDenylistPassthrough:
    def test_git_push_not_approved(self):
        assert_passthrough(run_hook("git push origin dev"))

    def test_git_push_bare_not_approved(self):
        assert_passthrough(run_hook("git push"))

    def test_git_merge_not_approved(self):
        assert_passthrough(run_hook("git merge main"))

    def test_git_rebase_not_approved(self):
        assert_passthrough(run_hook("git rebase dev"))

    def test_make_release_not_approved(self):
        assert_passthrough(run_hook("make release NEW=v1.0.0"))

    def test_make_ship_not_approved(self):
        assert_passthrough(run_hook("make ship"))


# ---------------------------------------------------------------------------
# Guard cases — tool_name, empty command, malformed JSON
# ---------------------------------------------------------------------------

class TestGuardPassthrough:
    def test_non_bash_tool_passthrough(self):
        assert_passthrough(run_hook("git add .", tool_name="Write"))

    def test_non_bash_edit_tool_passthrough(self):
        assert_passthrough(run_hook("git add .", tool_name="Edit"))

    def test_empty_command_passthrough(self):
        r = run_hook("")
        assert_passthrough(r)

    def test_malformed_json_passthrough(self):
        r = run_hook_raw("{not valid json")
        assert_passthrough(r)

    def test_missing_tool_input_passthrough(self):
        hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
        event = {"tool_name": "Bash"}  # no tool_input key
        r = subprocess.run(
            [sys.executable, hook],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        assert_passthrough(r)


# ---------------------------------------------------------------------------
# Output schema — session destination and permissions list shape
# ---------------------------------------------------------------------------

class TestOutputSchema:
    def test_session_destination_in_output(self):
        r = run_hook("git add .")
        payload = json.loads(r.stdout)
        assert payload["decision"]["updatedPermissions"]["destination"] == "session"

    def test_permissions_list_contains_bash_tool(self):
        r = run_hook("git add .")
        payload = json.loads(r.stdout)
        perms = payload["decision"]["updatedPermissions"]["permissions"]
        assert isinstance(perms, list)
        assert len(perms) == 1
        assert perms[0]["tool"] == "Bash"

    def test_permissions_command_field_present(self):
        r = run_hook("git add .")
        payload = json.loads(r.stdout)
        perms = payload["decision"]["updatedPermissions"]["permissions"]
        assert "command" in perms[0]

    def test_exit_code_always_zero_on_allow(self):
        r = run_hook("make test-unit")
        assert r.returncode == 0

    def test_exit_code_always_zero_on_passthrough(self):
        r = run_hook("git push origin dev")
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Anchoring — compound commands must not spoof a safe prefix
# ---------------------------------------------------------------------------

class TestAnchoringBehaviour:
    def test_compound_push_first_not_approved(self):
        # git push comes first — re.match on full string must NOT match git add\b
        assert_passthrough(run_hook("git push && git add ."))

    def test_compound_release_first_not_approved(self):
        assert_passthrough(run_hook("make release && make test"))

    def test_whitespace_normalisation_still_approves(self):
        # Extra spaces between tokens — normalise then match
        assert_approved(run_hook("git  add  ."))

    def test_tab_normalisation_still_approves(self):
        assert_approved(run_hook("git\tadd\t."))


# ---------------------------------------------------------------------------
# hooks.json registration
# ---------------------------------------------------------------------------

class TestHooksJsonRegistration:
    def test_permission_request_stanza_exists(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        assert "PermissionRequest" in hooks["hooks"], (
            "PermissionRequest stanza missing from hooks.json"
        )

    def test_permission_request_matcher_is_bash(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        stanza = hooks["hooks"]["PermissionRequest"]
        assert isinstance(stanza, list)
        assert stanza[0]["matcher"] == "Bash"

    def test_permission_request_command_points_to_hook(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        stanza = hooks["hooks"]["PermissionRequest"]
        cmd = stanza[0]["hooks"][0]["command"]
        assert "sdlc-permissions.py" in cmd

    def test_permission_request_uses_plugin_root_var(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        stanza = hooks["hooks"]["PermissionRequest"]
        cmd = stanza[0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in cmd

    def test_existing_stanzas_intact(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks["hooks"], (
                f"Existing stanza '{key}' was removed from hooks.json"
            )
