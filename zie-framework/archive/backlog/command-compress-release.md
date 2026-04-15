---
tags: [chore]
---

# Compress Release Command

## Problem

`/release` is 769 words with verbose gate specification and semver bump rules:
- Parallel gate logic described in 30 lines could be 5 lines
- Semver bump rules repeated when model already knows semver

Estimated reduction: ~249 words → ~520 words remaining.

## Motivation

Release fires at pipeline end. Compressing it reduces context cost at a critical workflow stage.

## Rough Scope

**In:**
- Compress parallel gate specification to concise instruction
- Compress semver bump rules to 1-line summary

**Out:**
- Changing release gate logic
- Changing semver calculation