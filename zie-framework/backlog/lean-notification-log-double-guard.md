# Backlog: Remove redundant type guard in notification-log.py

**Problem:**
notification-log.py has a double check for `notification_type == "permission_prompt"`:
1. Outer guard at line 22 exits if type != "permission_prompt"
2. Inner check at line 68 checks the same condition again

hooks.json already registers this hook with matcher "permission_prompt" so it will
only receive permission_prompt events. Both the outer guard and inner check are
redundant with the matcher.

**Rough scope:**
- Remove inner type check at line 68 (the outer guard at line 22 is sufficient)
- Add comment explaining: hook.json matcher ensures only permission_prompt events arrive
- Tests: no functional change, code-smell fix only
