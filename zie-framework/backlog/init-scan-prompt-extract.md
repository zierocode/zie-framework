---
tags: [chore]
---

# init.md Agent Scan Prompt Extraction

## Problem

`commands/init.md` is the largest file at 1,857 words. ~400 words of that is a
self-contained agent prompt block (lines 68–115) for the Explore agent's codebase scan.
This prompt is embedded inline in the command, making the command harder to read and
difficult to iterate on the prompt separately from the command logic.

Two other sources of bloat: the re-run guard explanation (80 words for 1 sentence of
logic) and the Makefile negotiation section (120 words for a 4-step flow).

## Motivation

Extracting the scan prompt to `templates/init-scan-prompt.md` and referencing it with
a single line reduces init.md by ~400 words and makes the prompt independently
editable without navigating the full command. The re-run guard and Makefile sections
can be compressed to checklists saving another ~100 words.

## Rough Scope

- Extract embedded agent prompt to `templates/init-scan-prompt.md`
- Replace the prompt block in init.md with: `Prompt: see templates/init-scan-prompt.md`
- Compress re-run guard to 2–3 lines; compress Makefile negotiation to a checklist
- Verify `test_commands_zie_init.py` assertions still pass (checks "SDLC pipeline:",
  "Migration complete:", pipeline stage list — none of these are in the agent prompt block)
