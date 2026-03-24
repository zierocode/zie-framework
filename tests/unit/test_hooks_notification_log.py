"""Tests for hooks/notification-log.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "notification-log.py")


def run_hook(event: dict, project_name: str, env_overrides: dict | None = None):
    """Run the hook with the given event dict and CLAUDE_CWD set to a fake project dir."""
    env = {
        **os.environ,
        "CLAUDE_CWD": f"/tmp/{project_name}",
    }
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def tmp_log_path(name: str, project: str) -> Path:
    """Mirror project_tmp_path logic for test assertions."""
    import re
    safe = re.sub(r"[^a-zA-Z0-9]", "-", project)
    return Path(f"/tmp/zie-{safe}-{name}")


# ---------------------------------------------------------------------------
# TestPermissionPromptLogging
# ---------------------------------------------------------------------------

class TestPermissionPromptLogging:
    def test_log_file_created_on_first_event(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Read file /etc/hosts"},
            project,
        )

        assert log.exists(), f"permission-log not created at {log}"

    def test_log_record_has_ts_and_msg(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Read file /etc/hosts"},
            project,
        )

        records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        assert len(records) == 1
        assert records[0]["msg"] == "Read file /etc/hosts"
        assert "ts" in records[0]

    def test_log_accumulates_multiple_events(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        for _ in range(2):
            run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )

        records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        assert len(records) == 2

    def test_no_stdout_on_first_two_occurrences(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        for _ in range(2):
            r = run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )
            assert r.stdout.strip() == "", f"Unexpected stdout on occurrence: {r.stdout!r}"

    def test_additional_context_injected_on_third_occurrence(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        # First two — no context
        for _ in range(2):
            run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )

        # Third — context must be injected
        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Read file /etc/hosts"},
            project,
        )
        assert r.stdout.strip() != "", "additionalContext expected on 3rd occurrence"
        payload = json.loads(r.stdout.strip())
        assert "additionalContext" in payload
        assert "/zie-permissions" in payload["additionalContext"]

    def test_additional_context_injected_on_fourth_and_beyond(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        for _ in range(3):
            run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )

        # Fourth occurrence — still injects
        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Read file /etc/hosts"},
            project,
        )
        payload = json.loads(r.stdout.strip())
        assert "additionalContext" in payload

    def test_count_is_per_message_not_total(self, tmp_path):
        """Different messages do not cross-contaminate counts."""
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        for _ in range(2):
            run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )
        # Different message — should NOT trigger context even though total log has 2+ entries
        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Write file /tmp/out"},
            project,
        )
        assert r.stdout.strip() == "", "Different message must not trigger context injection"

    def test_missing_message_key_treated_as_empty_string(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)

        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt"},
            project,
        )
        assert r.returncode == 0
        records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        assert records[0]["msg"] == ""

    def test_corrupted_log_resets_to_empty(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.write_text("not valid json\nmore garbage\n")

        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "some permission"},
            project,
        )
        assert r.returncode == 0
        records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        # After reset, only the new record should be present
        assert len(records) == 1
        assert records[0]["msg"] == "some permission"


# ---------------------------------------------------------------------------
# TestIdlePromptLogging
# ---------------------------------------------------------------------------

class TestIdlePromptLogging:
    def test_idle_log_created(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("idle-log", project)
        log.unlink(missing_ok=True)

        run_hook(
            {"event": "Notification", "notification_type": "idle_prompt",
             "message": "Session has been idle"},
            project,
        )
        assert log.exists(), f"idle-log not created at {log}"

    def test_idle_log_record_has_ts_and_msg(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("idle-log", project)
        log.unlink(missing_ok=True)

        run_hook(
            {"event": "Notification", "notification_type": "idle_prompt",
             "message": "Session has been idle"},
            project,
        )
        records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        assert records[0]["msg"] == "Session has been idle"
        assert "ts" in records[0]

    def test_idle_no_stdout(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("idle-log", project)
        log.unlink(missing_ok=True)

        r = run_hook(
            {"event": "Notification", "notification_type": "idle_prompt",
             "message": "Session has been idle"},
            project,
        )
        assert r.stdout.strip() == "", f"idle_prompt must not produce stdout: {r.stdout!r}"


# ---------------------------------------------------------------------------
# TestUnknownNotificationType
# ---------------------------------------------------------------------------

class TestUnknownNotificationType:
    def test_unknown_type_exits_zero_no_output(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        r = run_hook(
            {"event": "Notification", "notification_type": "auth_success",
             "message": "Login ok"},
            project,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_notification_type_exits_zero(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        r = run_hook({"event": "Notification"}, project)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# TestGuardrails
# ---------------------------------------------------------------------------

class TestGuardrails:
    def test_bad_stdin_exits_zero(self):
        """Malformed JSON on stdin must not crash the hook."""
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not json",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_always_exits_zero(self, tmp_path):
        project = f"testproj-{tmp_path.name}"
        r = run_hook(
            {"event": "Notification", "notification_type": "permission_prompt",
             "message": "Read file /etc/hosts"},
            project,
        )
        assert r.returncode == 0

    def test_symlink_at_log_path_logs_stderr_exits_zero(self, tmp_path):
        """If the log path is a symlink, safe_write_tmp refuses and hook still exits 0."""
        project = f"testproj-{tmp_path.name}"
        log = tmp_log_path("permission-log", project)
        log.unlink(missing_ok=True)
        # Create a symlink pointing somewhere harmless
        target = tmp_path / "real_file.txt"
        target.write_text("")
        log.symlink_to(target)

        try:
            r = run_hook(
                {"event": "Notification", "notification_type": "permission_prompt",
                 "message": "Read file /etc/hosts"},
                project,
            )
            assert r.returncode == 0
        finally:
            log.unlink(missing_ok=True)

    def test_two_tier_error_pattern_in_source(self):
        """Hook source must contain the two-tier error pattern: outer except + inner except."""
        source = Path(HOOK).read_text()
        assert "sys.exit(0)" in source, "Outer guard must call sys.exit(0) on parse failure"
        assert "[zie-framework] notification-log:" in source, (
            "Inner operations must log to stderr with [zie-framework] notification-log: prefix"
        )


# ---------------------------------------------------------------------------
# TestHooksJsonRegistration
# ---------------------------------------------------------------------------

class TestHooksJsonRegistration:
    HOOKS_JSON = Path(REPO_ROOT) / "hooks" / "hooks.json"

    def _load(self):
        return json.loads(self.HOOKS_JSON.read_text())

    def test_notification_key_exists(self):
        data = self._load()
        assert "Notification" in data["hooks"], (
            "hooks.json must have a 'Notification' key under 'hooks'"
        )

    def test_permission_prompt_matcher_registered(self):
        data = self._load()
        matchers = [entry.get("matcher") for entry in data["hooks"]["Notification"]]
        assert "permission_prompt" in matchers, (
            "Notification hooks must include a 'permission_prompt' matcher"
        )

    def test_idle_prompt_matcher_registered(self):
        data = self._load()
        matchers = [entry.get("matcher") for entry in data["hooks"]["Notification"]]
        assert "idle_prompt" in matchers, (
            "Notification hooks must include an 'idle_prompt' matcher"
        )

    def test_both_matchers_point_to_notification_log(self):
        data = self._load()
        for entry in data["hooks"]["Notification"]:
            for hook in entry.get("hooks", []):
                assert "notification-log.py" in hook.get("command", ""), (
                    f"Notification hook entry must reference notification-log.py: {hook}"
                )

    def test_existing_events_unchanged(self):
        data = self._load()
        hooks = data["hooks"]
        for event in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert event in hooks, f"Existing event '{event}' must still be present in hooks.json"

    def test_notification_output_protocol_documented(self):
        data = self._load()
        protocol = data.get("_hook_output_protocol", {})
        assert "Notification" in protocol, (
            "_hook_output_protocol must document the Notification output format"
        )
