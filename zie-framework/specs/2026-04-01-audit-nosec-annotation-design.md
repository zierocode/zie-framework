---
slug: audit-nosec-annotation
status: approved
date: 2026-04-01
---
# Spec: Document nosec B310 suppression in call_zie_memory_api

## Problem

`hooks/utils.py:416` contains:

```python
urllib.request.urlopen(req, timeout=timeout)  # nosec B310
```

The bare `# nosec B310` annotation suppresses Bandit's B310 check (urllib
`urlopen` with a non-literal URL) with no explanation of why the suppression is
safe. Both callers of this function validate the URL starts with `https://`
before passing it here, so the actual risk is low — but the annotation leaves a
future reader (or auditor) unable to verify that assumption without tracing call
sites. If the https-prefix guard were ever removed or bypassed, the suppression
would silently hide the regression.

## Proposed Solution

Append an inline justification to the existing nosec annotation on
`hooks/utils.py:416`, changing:

```python
urllib.request.urlopen(req, timeout=timeout)  # nosec B310
```

to:

```python
urllib.request.urlopen(req, timeout=timeout)  # nosec B310 — URL validated as https:// by caller before reaching this function
```

No logic changes. No new imports. No structural changes to the function. The
annotation text makes the suppression self-explaining and auditable in-place.

After the change, run `bandit -r hooks/` to confirm B310 is still suppressed
and no new issues are introduced.

## Acceptance Criteria

- [ ] AC1: `hooks/utils.py:416` ends with `# nosec B310 — URL validated as https:// by caller before reaching this function` (exact text).
- [ ] AC2: The surrounding code (lines 410–416) is otherwise unchanged — no logic, import, or whitespace differences outside the comment.
- [ ] AC3: `bandit -r hooks/` exits 0 (or exits with the same non-zero code as before the change, if other pre-existing issues exist) and reports no B310 issue on `utils.py:416`.
- [ ] AC4: The existing test suite (`make test-fast`) passes with no new failures.

## Out of Scope

- Changing any call sites or adding URL-validation logic inside `call_zie_memory_api`.
- Suppressing or addressing any other Bandit findings.
- Adding type annotations, docstrings, or other improvements to `utils.py`.
- Updating README or CLAUDE.md (no documented behavior changes).
