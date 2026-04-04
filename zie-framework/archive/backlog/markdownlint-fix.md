# Fix markdownlint-cli Pre-commit Hook

## Problem

`markdownlint-cli@0.48.0` in `.pre-commit-config.yaml` is broken — it always
prints the help text and exits 0 regardless of file content. The markdown lint
gate appears to run but catches nothing.

## Motivation

A silently-disabled lint gate is worse than no gate — it creates false
confidence. Pinning to a working version or switching to `markdownlint-cli2`
restores the gate and allows markdown style violations to block commits.

## Rough Scope

- Identify a working version of `markdownlint-cli` or evaluate `markdownlint-cli2`
- Update `.pre-commit-config.yaml` to pin the working version
- Verify the gate fails on a file with known violations (e.g., missing blank
  line before heading) and exits 0 on clean files
- Out of scope: changing markdown rules or adding new lint checks
