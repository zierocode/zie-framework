# safety_check_agent: Use COMPILED_BLOCKS in Fallback Path

## Problem

`safety_check_agent.py:44` uses a raw `re.search` loop over `BLOCKS` (string list) in the regex fallback path, bypassing `COMPILED_BLOCKS` which `utils_safety` exports specifically for pre-compiled reuse. Each call to the fallback path recompiles all block patterns instead of using the module-level compiled cache.

## Motivation

`COMPILED_BLOCKS` exists to avoid recompilation overhead. Using raw patterns in the fallback path is inconsistent with the rest of the codebase and wastes the optimization. One-line fix to use the pre-compiled version.

## Rough Scope

- Replace `re.search(p, command)` loop over `BLOCKS` with the pre-compiled `COMPILED_BLOCKS` patterns in `safety_check_agent.py`
- Import `COMPILED_BLOCKS` from `utils_safety` if not already imported
