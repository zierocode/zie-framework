# Backlog: Suppress intent-sdlc injection when user is mid-command

**Problem:**
intent-sdlc.py fires on every UserPromptSubmit and injects SDLC state into context
regardless of whether Claude is mid-command (which already has full context from its
SKILL.md). The early-exit guard only skips messages with first token shorter than 20
chars — a command like `/sprint slug1 slug2 --dry-run` does NOT early-exit. The
full SDLC state string is injected into context that already carries the command's
own instructions, adding noise.

**Motivation:**
Every command invocation currently receives both the command's own context AND the
intent-sdlc SDLC state injection. The injection is pure redundancy — the command
already knows the SDLC state from its own instructions. Fix: extend early-exit to
any message where `message.split()[0].startswith("/")` regardless of length.
~100–200 tokens saved per command invocation.

**Rough scope:**
- Change intent-sdlc.py early-exit guard from `len(first_token) < 20` to
  `first_token.startswith("/")`
- Verify the guard correctly skips all slash commands including those with args
- Tests: UserPromptSubmit with `/sprint foo bar` → hook exits without injecting
