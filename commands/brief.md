---
description: Display the active design brief from .zie/handoff.md, or report when none exists.
argument-hint: ""
allowed-tools: Read
model: sonnet
effort: low
---

# /brief — Design Brief Review

Display the captured design brief and confirm readiness for `/sprint`.

<!-- preflight: minimal -->

## Steps

1. Check `$CWD/.zie/handoff.md`:
   - If absent → print:
     ```
     No active design brief — run a design conversation first,
     or invoke zie-framework:brainstorm to start a structured session.
     ```
   - If present → display brief, then: → /sprint to execute
     Stop here.

2. Read `.zie/handoff.md` — display its full content formatted.

3. Print:
   ```
   Brief captured at: <captured_at value>
   Source: <source value>

   Run /sprint <feature-name> to start the pipeline with this brief.
   Run /sprint without arguments to be prompted for a topic.
   ```
