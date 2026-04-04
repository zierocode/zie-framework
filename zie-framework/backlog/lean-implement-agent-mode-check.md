# Backlog: Simplify /implement agent-mode pre-flight (non-blocking)

**Problem:**
implement.md Step 0 prints a multi-line warning and asks a yes/no question on every
run outside of `--agent zie-framework:zie-implement-mode`. This adds an interactive
round-trip before any real work starts — every normal session user hits this gate.

**Motivation:**
The agent-mode recommendation is valid guidance but the blocking prompt adds friction
and ~100–200 tokens of preamble to every /implement invocation. A non-blocking
advisory note at the top (or bottom) achieves the same goal without stalling the flow.

**Rough scope:**
- Replace blocking yes/no gate with a single advisory line: "Tip: run inside
  `claude --agent zie-framework:zie-implement-mode` for best results."
- Remove the wait-for-confirmation step
- Tests: structural test asserting Step 0 does not contain blocking user prompt
