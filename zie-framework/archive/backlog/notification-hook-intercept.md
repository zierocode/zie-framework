# Backlog: Notification Hook — Intercept Permission Dialogs

**Problem:**
When Claude Code shows a permission prompt (`permission_prompt` notification),
the user has to manually respond. For zie-framework sessions in "implement mode"
where all operations are expected to be safe, these dialogs are friction.

**Motivation:**
`Notification` hooks fire on `permission_prompt`, `idle_prompt`,
`auth_success`, and `elicitation_dialog` events. They can inject
`additionalContext` to give Claude more information, or they can be used
to log/track permission patterns for later analysis.

**Rough scope:**
- New hook: `hooks/notification-log.py` (Notification event, async: true)
- Matcher: `permission_prompt`
- Log: notification message + timestamp to `project_tmp_path("permission-log")`
- If the same permission is prompted 3+ times in a session → inject
  `additionalContext`: "This permission has been asked repeatedly. Consider
  running /zie-permissions to add it to the allow list."
- `idle_prompt` matcher: log idle events for session analytics
- Tests: log written, repeat-prompt detection, async non-blocking
