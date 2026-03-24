# Backlog: PermissionRequest Auto-Approve for Safe SDLC Operations

**Problem:**
Claude Code prompts for permission on routine SDLC operations: `git add`,
`git commit`, `make test-unit`, `python3 -m pytest`. During a TDD loop these
interruptions happen dozens of times per session, breaking flow.

**Motivation:**
`PermissionRequest` hooks can output `decision.behavior: "allow"` with
`updatedPermissions` to auto-approve patterns and persist them for the session.
One-time approval per session for well-known safe patterns eliminates all
subsequent prompts.

**Rough scope:**
- New hook: `hooks/sdlc-permissions.py` (PermissionRequest event)
- Matcher: `Bash`
- Safe allowlist: `git add`, `git commit -m`, `make test*`, `make lint*`,
  `python3 -m pytest`, `python3 -m bandit`
- Output: `allow` + `updatedPermissions` with `destination: "session"` so the
  rule persists for the rest of the session (no repeated prompts)
- Explicitly NOT auto-approved: git push, git merge, make release
- Tests: allowlist matches, non-safe patterns still prompt, session persistence
