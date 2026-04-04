# Backlog: Standardize version pinning strategy in requirements-dev.txt

**Problem:**
requirements-dev.txt uses `>=` (lower-bound) for all packages except ruff which is
exact-pinned at `==0.11.2`. This creates a split policy: `pytest>=9.0.3` allows any
future major, while `ruff==0.11.2` blocks Dependabot auto-PRs from auto-merging.

**Rough scope:**
- Decide on one strategy: `~=` (compatible release) for all, or `>=` for all
- Update requirements-dev.txt to use consistent pinning
- Document the chosen strategy in a comment
- Tests: CI should reproduce with exact locked versions (use pip-compile or similar)
