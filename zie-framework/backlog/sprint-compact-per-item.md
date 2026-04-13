# sprint-compact-per-item — /compact After Each Phase 2 Item

## Problem

Sprint Phase 2 (impl) accumulates conversation history across all items in sequence. By item 2 or 3, the context window is already partially filled from item 1's implementation, tests, and reviewer output. This leaves less headroom for subsequent items and increases the probability of context overflow before Phase 3 (release) is reached.

## Motivation

Each impl item is self-contained — the conversation history of item N provides no value when implementing item N+1 (the plan file is re-read fresh anyway). Running `/compact` between items clears accumulated history and maximizes available context for the next item and for Phase 3+4.

## Rough Scope

- Modify `commands/sprint.md` Phase 2 loop: after each item's impl + commit succeeds, run `/compact` before starting the next item
- Do NOT compact before the first item (context is fresh at Phase 2 start)
- Do NOT compact after the last item (Phase 3 already has its own compact checkpoint)
- Print `[compact] context cleared after <slug>` to signal the action
