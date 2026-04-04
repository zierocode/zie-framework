# failure-context: Add zie-framework Existence Guard Before Expensive Operations

## Problem

`failure-context.py:39-43` immediately calls `load_config`, reads ROADMAP, and runs 2 git subprocess calls after the outer guard — without first checking that `zie-framework/` exists in `cwd`. All other hooks that touch ROADMAP or git perform this check first. In a project without zie-framework initialized, every tool failure triggers 2 git subprocesses and a file read that return empty results.

## Motivation

Defensive guard prevents unnecessary work in uninitialized projects. Consistent with how all other hooks handle the uninitialized case — early exit at the `zie-framework/` check before any I/O.

## Rough Scope

- Add `if not (Path(cwd) / "zie-framework").exists(): sys.exit(0)` before the inner operations in `failure-context.py`
- Place it after the outer guard, before `load_config`
- Update tests to cover uninitialized project path
