# Backlog: PostToolUseFailure — Inject Debugging Context on Failure

**Problem:**
When a tool fails (test run crashes, file write fails, bash errors), Claude
sees the raw error and has to investigate from scratch. No SDLC context is
available at the point of failure.

**Motivation:**
`PostToolUseFailure` supports `additionalContext` injection. Injecting context
at the moment of failure (what task was active, which test was being run, recent
git changes) dramatically reduces the number of turns needed to diagnose the
issue.

**Rough scope:**
- New hook: `hooks/failure-context.py` (PostToolUseFailure event)
- Matcher: `Bash|Write|Edit`
- On failure: read ROADMAP Now lane, last git log entry, current branch
- Output `additionalContext`: active task + last commit + "check tests: make
  test-unit" + is_interrupt info
- Handle `is_interrupt: true` separately (user interrupted — no debug context)
- Register in `hooks/hooks.json`
- Tests: context output structure, interrupt case, missing ROADMAP graceful
