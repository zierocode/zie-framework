---
name: test-pyramid
description: Testing strategy by project type — which tests to write, when to run them
type: reference
user-invocable: false
argument-hint: ""
model: haiku
effort: low
---

# Test Pyramid — zie-framework

## The Pyramid

```text
         /\
        /E2E\          → Playwright — user journeys, /zie-release only
       /------\
      /  INTG  \       → Real DB/services, /zie-release only
     /----------\
    / UNIT TESTS \     → Every PostToolUse:Edit, /zie-implement constant
   /--------------\
```

## แยกตาม Project Type

### python-api (e.g., zie-memory)

**Unit tests** (`tests/` — no `integration` marker):

- Pure logic: search algorithms, score computation, data transforms
- Mock external services (DB, HTTP)
- Target: < 5s total, < 1s per test
- Run: `pytest tests/ -x -q -m "not integration"`

**Integration tests** (`tests/` — `@pytest.mark.integration`):

- Real PostgreSQL — test queries, migrations, constraints
- Real HTTP — test API endpoints end-to-end via TestClient
- Skip if `TEST_DB_AVAILABLE` not set
- Run: `TEST_DB_AVAILABLE=1 pytest tests/ -m "integration" -v`

**E2E** (if HTMX dashboard present — `playwright_enabled=true`):

- Dashboard loads, search works, memory CRUD via UI
- Run: `npx playwright test tests/e2e/`

### typescript-fullstack (Next.js, etc.)

**Unit tests** (vitest):

- Components (React Testing Library), utilities, hooks
- No real network, no real DB
- Run: `npx vitest run --reporter=dot`

**Integration tests** (vitest or supertest):

- API route handlers with real DB (or test DB)
- Run: `npx vitest run --project=integration`

**E2E** (Playwright — always enabled):

- Critical user journeys only: auth, core CRUD, payment flow
- Not every component — only flows that break silently
- Run: `npx playwright test`

### cli-tool / python-script

**Unit tests** only:

- Input validation, output formatting, core logic
- Subprocess tests for CLI invocation
- No E2E needed (CLI = the E2E)

## ควรรัน Test ไหนเมื่อไหร่

| Trigger | Tests to run |
| --- | --- |
| Every file save (PostToolUse hook) | Unit only (auto, fast) |
| /zie-implement task complete | Unit only |
| /zie-implement all tasks complete | Unit + Integration |
| /zie-release gate | Unit + Integration + E2E + Visual |
| Debugging a failing test | Relevant unit only |

