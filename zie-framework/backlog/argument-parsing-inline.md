---
tags: [chore]
---

# Argument Parsing Block Compression

## Problem

Commands with optional flags (spec.md `--draft-plan`, sprint.md `--dry-run`/`--skip-ready`/`--version=`) 
each contain verbose Python-style argument parsing blocks (~80–120 words) that explain how to 
split and extract flags. The actual usage of the parsed values is only 1–2 sentences per flag.
The parsing overhead outweighs the feature description.

## Motivation

Inlining flag logic at the point of use ("if `--draft-plan` present → invoke write-plan")
rather than pre-declaring a parsing block saves ~200–300 words and reduces the distance
between flag declaration and usage. A brief argument table replaces the parsing prose.

## Rough Scope

- Replace Python parsing blocks in spec.md and sprint.md with a 1-row-per-flag table
- Move flag handling inline where the flag is used (e.g., step 4 for --draft-plan)
- Verify test_workflow_lean.py (checks `--draft-plan`, `write-plan`, `clean_args` in spec.md)
  and test_zie_sprint.py (checks `--dry-run`, `--skip-ready`, `--version=`) still pass
