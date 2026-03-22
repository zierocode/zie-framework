---
name: test-pyramid
description: Testing strategy by project type — which tests to write, when to run them
type: reference
---

# Test Pyramid — zie-framework

## The Pyramid

```text
         /\
        /E2E\          → Playwright — user journeys, /zie-ship only
       /------\
      /  INTG  \       → Real DB/services, /zie-ship only
     /----------\
    / UNIT TESTS \     → Every PostToolUse:Edit, /zie-build constant
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
| /zie-build task complete | Unit only |
| /zie-build all tasks complete | Unit + Integration |
| /zie-ship gate | Unit + Integration + E2E + Visual |
| Debugging a failing test | Relevant unit only |

## เขียน Test ที่ดี

**Name tests as behavior, not implementation:**

- BAD: `test_hybrid_search_function`
- GOOD: `test_should_return_most_relevant_memory_first`

**Focus E2E on user journeys, not page coverage:**

- BAD: "test every page loads"
- GOOD: "test user can save a memory and find it by search"

**Integration tests must use real external services:**

- Real PostgreSQL (not SQLite)
- Real HTTP calls via TestClient (not mocked)
- If it can't run without infrastructure, mark it `@pytest.mark.integration`

## Playwright Specifics

```typescript
// tests/e2e/fixtures.ts — shared setup
import { test as base } from '@playwright/test';
export const test = base.extend({ /* project fixtures */ });

// Focus on user journeys
test('user can search memories', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="search-input"]', 'vue framework');
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

**`playwright.config.ts` essentials:**

- `baseURL` from env (works locally + CI)
- `retries: 1` in CI (catch flaky tests, not hide them)
- `screenshot: 'only-on-failure'`
- `video: 'retain-on-failure'`
- Run on chromium only for speed (add more for pre-release only)
