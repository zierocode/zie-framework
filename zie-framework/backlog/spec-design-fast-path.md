# spec-design Fast Path for Complete Backlog Items

## Problem

`spec-design` always asks 4 clarifying questions one at a time before
proposing any approach — even when the backlog item already has a complete
Problem, Motivation, and Rough Scope. For well-defined items this adds 4
unnecessary round-trips before any real design work begins.

## Motivation

The clarifying questions exist to fill gaps. When there are no gaps, they
are friction. A fast path that detects complete backlog items and skips
directly to approach proposal cuts the spec session significantly for the
common case where the developer already knows what they want.

## Rough Scope

- In `spec-design`: read the backlog item's Problem, Motivation, and Rough
  Scope sections — if all three are substantive (not empty or one word),
  skip clarifying questions and proceed directly to proposing 2-3 approaches
- If any section is thin or missing → fall through to normal question flow
- Out of scope: changing the approach proposal or design section steps
