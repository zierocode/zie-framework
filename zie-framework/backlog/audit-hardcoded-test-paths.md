---
tags: [bug]
---

# Fix Hardcoded Absolute Paths in Test Files

## Problem

Two test files contain hardcoded `/Users/zie/Code/zie-framework` paths — tests fail on any other machine or CI environment.

## Motivation

CI portability and contributor onboarding. Tests should pass regardless of the developer's local path.

## Rough Scope

- Fix `tests/unit/test_utils_submodules_importable.py:7` and `tests/unit/test_knowledge_hash_now.py:9,15,25,35`
- Use `os.path.dirname(__file__)` or `pathlib.Path(__file__).parent` for relative path resolution