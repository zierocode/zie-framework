# spec-design Batch Section Approval

## Problem

`spec-design` presents and seeks approval after each design section
sequentially: Problem → Architecture → Data Flow → Edge Cases → Out of
Scope. Five separate approval round-trips to write one spec document.

## Motivation

Sequential section approval made sense when specs were being co-authored
interactively. In practice, the developer rarely rejects a single section
mid-spec — they review the whole thing at the end. Writing all sections in
one pass and asking for a single consolidated review cuts 4 unnecessary
interruptions per spec.

## Rough Scope

- In `spec-design`: draft all sections (Problem, Architecture, Data Flow,
  Edge Cases, Out of Scope) in one pass without intermediate approval prompts
- Present the complete draft to the user once for review/edit
- User can request changes to any section — apply all at once, re-present
- Proceed to spec-reviewer only after user accepts the full draft
- Out of scope: changing what sections are in the spec
