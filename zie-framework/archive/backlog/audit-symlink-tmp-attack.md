# Symlink attack on /tmp state files

**Severity**: High | **Source**: audit-2026-03-24

## Problem

`auto-test.py` and `wip-checkpoint.py` write to paths returned by
`project_tmp_path()` without first checking if the target is a symlink. A local
user can pre-create a symlink `zie-{project}-{name}` → `~/.ssh/config` (or any
writable file) and the hook will overwrite it.

## Motivation

On shared developer machines or CI containers with multiple users, this is a real
vector. Fix: use `os.path.islink()` check before writing, or use `O_NOFOLLOW`
flag via `os.open()`.
