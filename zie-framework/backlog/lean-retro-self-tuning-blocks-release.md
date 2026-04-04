# Backlog: Move retro self-tuning proposals to advisory note (non-blocking)

**Problem:**
retro.md "Self-tuning proposals" section (lines 108–124) runs inline between ADR
writes and auto-commit. It prints proposals then waits for user to type "apply" or
skip — a synchronous blocking interaction mid-flow. Since retro runs automatically
from /release (step 11), this blocking prompt stalls the automated release pipeline
mid-stream until the user responds.

**Motivation:**
Self-tuning is a useful feature but should not block the critical path (ADR commit,
ROADMAP update, version bump). The user is in the middle of a release — not the
right moment for interactive framework tuning. Moving it to a non-blocking advisory
at the very end preserves the feature while unblocking the pipeline.

**Rough scope:**
- Move self-tuning proposal print to the final step of retro (after commit, after
  ROADMAP update, after all blocking work is done)
- Remove the blocking "apply/skip" wait — replace with: "To apply: run /chore
  with the proposal above"
- Add a configurable opt-out via .config key (e.g., `self_tuning_enabled: false`)
- Tests: retro flow completes without blocking user input
