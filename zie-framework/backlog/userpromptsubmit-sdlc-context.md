# Backlog: UserPromptSubmit SDLC Context Injection

**Problem:**
zie-framework's `intent-detect.py` fires only when Claude decides to run a
Bash command — too late. Claude has already processed the user prompt without
knowing the current SDLC state (active task, stage, next step). This causes
Claude to give generic answers instead of SDLC-aware guidance.

**Motivation:**
`UserPromptSubmit` fires on every user message, before Claude processes it.
Injecting SDLC state here means Claude always knows what stage we're in,
what task is active, and what the next suggested action is — with zero extra
turns required.

**Rough scope:**
- New hook: `hooks/sdlc-context.py` (UserPromptSubmit event)
- Read ROADMAP Now lane, current git branch, test status
- Output `additionalContext` with: active task, stage, suggested next command,
  and whether tests are stale
- Fast: must complete in < 100ms (no subprocess, pure file reads)
- Replace or subsume the `intent-detect.py` SDLC-awareness portion
- Register in `hooks/hooks.json` (no matcher — fires on all prompts)
- Tests: hook output structure, empty ROADMAP edge case, fast execution bound
