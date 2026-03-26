# Security: Path Traversal Fixes in input-sanitizer.py

**Source**: audit-2026-03-24b H2 + M13 (Agent A + Agent C)
**Effort**: S
**Score impact**: +8 (High eliminated → Security +8)

## Problem

`hooks/input-sanitizer.py:58` validates file_path boundaries using string prefix
matching:

```python
if not str(abs_path).startswith(str(cwd)):
```

This has a known false-negative: if `cwd=/home/user` and
`abs_path=/home/user-evil/file.txt`, `startswith()` incorrectly passes. The
correct check is `Path.is_relative_to()` (Python 3.9+) which compares path
components, not string prefixes.

Additionally, no tests cover:
- Symlink loops in `file_path` (`.resolve()` may hang)
- NUL bytes in path (`\x00` truncates C-style strings)
- Unicode normalization exploits (e.g., `%2e%2e`)

## Motivation

Path traversal could allow Claude to write files outside the project root when
given a crafted relative path. While Claude controls the input, defense-in-depth
requires the boundary check to be correct.

## Scope

- `hooks/input-sanitizer.py:58`: replace `startswith()` with `abs_path.is_relative_to(cwd)`
- Add `.resolve()` timeout guard or symlink depth limit
- Add tests: `user-evil` prefix edge case, NUL byte path, symlink loop path

## Acceptance Criteria

- [ ] `is_relative_to()` used for boundary check
- [ ] `/home/user-evil/file.txt` correctly rejected when cwd is `/home/user`
- [ ] Tests for all 3 edge cases
- [ ] Existing path traversal tests still pass
