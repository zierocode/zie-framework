---
name: test-pyramid
description: Testing strategy by project type — which tests to write, when to run them
user-invocable: false
argument-hint: ""
model: haiku
effort: low
---

# Test Pyramid — zie-framework

## The Pyramid

```text
         /\
        /E2E\          → Playwright — user journeys, /release only
       /------\
      /  INTG  \       → Real DB/services, /release only
     /----------\
    / UNIT TESTS \     → Every PostToolUse:Edit, /implement constant
   /--------------\
```

## แยกตาม Project Type

### python-api (e.g., zie-memory)

**Unit** (`tests/` — no `integration` marker):
- Pure logic: search, scoring, transforms
- Mock external services (DB, HTTP)
- Target: < 5s total, < 1s/test
- Run: `pytest tests/ -x -q -m "not integration"`

**Integration** (`tests/` — `@pytest.mark.integration`):
- Real PostgreSQL — queries, migrations, constraints
- Real HTTP — API endpoints via TestClient
- Skip if `TEST_DB_AVAILABLE` not set
- Run: `TEST_DB_AVAILABLE=1 pytest tests/ -m "integration" -v`

**E2E** (if `playwright_enabled=true`):
- Dashboard loads, search, memory CRUD via UI
- Run: `npx playwright test tests/e2e/`

### typescript-fullstack (Next.js, etc.)

**Unit** (vitest):
- Components (React Testing Library), utilities, hooks
- No real network/DB
- Run: `npx vitest run --reporter=dot`

**Integration** (vitest or supertest):
- API route handlers with real/test DB
- Run: `npx vitest run --project=integration`

**E2E** (Playwright — always enabled):
- Critical journeys only: auth, core CRUD, payment
- Not every component — only flows that break silently
- Run: `npx playwright test`

### cli-tool / python-script

**Unit only**:
- Input validation, output formatting, core logic
- Subprocess tests for CLI invocation
- No E2E needed (CLI = the E2E)

## ควรรัน Test ไหนเมื่อไหร่

| Trigger | Tests |
| --- | --- |
| Every file save (PostToolUse hook) | Unit only (auto, fast) |
| /implement task complete | Unit only |
| /implement all tasks complete | Unit + Integration |
| /release gate | Unit + Integration + E2E + Visual |
| Debugging a failing test | Relevant unit only |