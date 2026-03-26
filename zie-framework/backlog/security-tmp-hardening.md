# Security: /tmp Hardening — Permissions, TOCTOU, Predictable Names

**Source**: audit-2026-03-24b H1 + H3 + M (Agent A, Bandit B108 x3)
**Effort**: M
**Score impact**: +8 (High eliminated → Security +8)

## Problem

Four related /tmp security issues:

1. **No file permissions enforcement**: `safe_write_tmp()`, `safe_write_persistent()`,
   and `atomic_write()` in `hooks/utils.py` create files with default umask
   (0o644 or 0o022), making `/tmp/zie-*` files world-readable. Session state
   (active task, edit counts, test results) leaks to other local users.

2. **TOCTOU in atomic_write**: Between `path.write_text()` and `os.replace()`,
   the `.tmp` suffix file is predictably named and replaceable in a race window.

3. **Predictable filenames**: `/tmp/zie-{project}-{name}` allows enumeration of
   active projects and targeted writes before hooks create them.

4. **session-cleanup.py:17** globs `/tmp` directly without using the utils wrapper,
   bypassing symlink protection.

## Motivation

Local information disclosure and potential state corruption. Bandit flags 3 Medium
findings (B108). Python tempfile docs and OpenSSF recommend unpredictable names.

## Scope

- `hooks/utils.py:57-65` (atomic_write): use `tempfile.NamedTemporaryFile(dir=...,
  mode=0o600)` + `os.replace()` for atomic+private writes
- `hooks/utils.py:107-126, 196-214` (safe_write_tmp/persistent): add
  `os.chmod(path, 0o600)` after write
- `hooks/session-cleanup.py:17`: route through utils wrapper instead of direct glob
- Consider `XDG_RUNTIME_DIR` or project-local `.cache/` as alternative to /tmp

## Acceptance Criteria

- [ ] All /tmp files created with 0o600 permissions
- [ ] atomic_write uses unpredictable temp suffix
- [ ] session-cleanup.py uses utils wrapper
- [ ] Bandit B108 findings resolved (0 Medium from hardcoded /tmp)
- [ ] Tests for permission enforcement and TOCTOU resistance
