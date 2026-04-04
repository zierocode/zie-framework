# Backlog: Suppress intent-sdlc SDLC state suffix when idle + intent clear

**Problem:**
intent-sdlc.py appends `task:none | stage:idle | next:/status | tests:unknown`
to every prompt injection when there is no active task and intent is unambiguous.
This ~60-char suffix is injected on every prompt during idle state — which is the
most common state between commands. It conveys zero information Claude doesn't
already know from the intent signal alone.

**Motivation:**
The SDLC state suffix (task/stage/next/tests) is only meaningful when something is
actively in flight. When stage=idle and task=none, the suffix is pure overhead on
every single UserPromptSubmit. Suppressing it conditionally (idle + unambiguous intent)
saves ~60 chars per prompt × every idle-state prompt in the session.

**Rough scope:**
- In intent-sdlc.py, make the SDLC state suffix conditional:
  only append when `stage != "idle"` OR `active_task != "none"`
- When idle + intent score ≥ 2 (unambiguous): emit only the intent signal, no state suffix
- When idle + intent score < 2 (ambiguous): keep full suffix to help Claude orient
- Tests: idle state + clear intent → no state suffix in output;
         active task → full suffix emitted
