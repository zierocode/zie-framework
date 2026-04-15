---
tags: [chore]
---

# Compress Sprint Command

## Problem

`/sprint` command is 2,108 words — the longest command file. Major verbosity sources:
- 4 embedded Python code blocks (~200 words) that could be prose descriptions
- Repeated "Read sprint context bundle" blocks (~80 words)
- Progress bar template repeated 4 times (~60 words)

Estimated reduction: ~900 words → ~1,200 words remaining.

## Motivation

Every word in a command file becomes token context when the command is invoked. Sprint is the most token-expensive command, and it fires during the most context-intensive workflow (batch pipeline).

## Rough Scope

**In:**
- Replace Python code blocks with concise prose instructions
- Factor "Read sprint context bundle" into a single reference
- Define progress bar format once, reference by name

**Out:**
- Changing sprint workflow steps
- Changing sprint output format