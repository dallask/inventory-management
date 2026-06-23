# Testing Patterns

**Analysis Date:** 2026-06-23

## Test Stack

**Runner:** pytest (Python) via `uv run pytest`
**HTTP Client:** FastAPI `TestClient` (wraps `httpx`, synchronous interface)
**Assertion:** Built-in `assert` statements — no external assertion library
**Coverage:** `pytest-cov` — minimum threshold enforced at 70%
**Linting/Format:** `ruff check` and `ruff format` run as a separate CI job

**Frontend:** No frontend unit test framework present. `package.json` has no test script, no vitest, no jest configuration. Frontend CI only runs `npm run build` to verify the build succeeds.

## Test Organization

**Location:** All backend tests live under `tests/backend/` at the project root — not co-located with source.

```
tests/
└── backend/
    ├── conftest.py              # Shared fixtures (client, sample data)
    ├── test_dashboard.py        # /api/dashboard/* endpoints
    ├── test_inventory.py        # /api/inventory endpoints
    ├── test_misc_endpoints.py   # /api/demand, /api/backlog, /api/spending
    ├── test_orders.py           # /api/orders endpoints
    └── test_reports.py          # /api/reports/* endpoints
```

**File naming:** `test_<resource>.py` — one file per API resource group.

**Test class naming:** `Test<Resource>Endpoints` — all tests are methods on a class (no module-level test functions).

**Test method naming:** `test_<what_is_being_verified>` — descriptive snake_case that reads as a sentence (e.g., `test_filter_by_warehouse_san_francisco`, `test_get_nonexistent_order_returns_404`).

## Test Types Present

**Integration tests only** — all tests hit the real FastAPI app via `TestClient`. There are no unit tests for individual functions or computed properties.

Each test:
1. Makes an HTTP request through `TestClient`
2. Asserts `response.status_code`
3. Parses `response.json()`
4. Asserts on response structure, types, and business logic

**Cross-endpoint consistency tests** are included in `test_orders.py` — for example, verifying that `pending_orders` in the dashboard summary matches the count of pending orders from `/api/orders`.

## Test Structure

**Fixture setup** (`tests/backend/conftest.py`):

```python
@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_inventory_item():
    """Sample inventory item for testing."""
    return { "id": "1", "sku": "PCB-001", ... }
```

**Test class structure** with section comments:

```python
class TestOrdersEndpoints:
    """Test suite for orders-related endpoints."""

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_get_all_orders(self, client):
        """Test getting all orders returns a non-empty list."""
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    # ── Warehouse filter ─────────────────────────────────────────────────────

    def test_filter_by_warehouse_san_francisco(self, client):
        """Test filtering orders to San Francisco warehouse only."""
        response = client.get("/api/orders?warehouse=San Francisco")
        data = response.json()
        for order in data:
            assert order["warehouse"] == "San Francisco"
```

**Section groupings used in `test_orders.py`:**
- Happy path
- Items sub-structure
- Single-resource retrieval
- Warehouse filter
- Status filter
- Month / quarter filter
- Combined filters
- Cross-endpoint consistency

## Coverage

**Minimum threshold:** 70% (enforced by `--cov-fail-under=70` in CI — build fails below this)

**Coverage report formats:** terminal (`--cov-report=term-missing`) and XML (`tests/coverage.xml`) uploaded as CI artifact

**What is covered:**
- All major API endpoints: `/api/inventory`, `/api/orders`, `/api/dashboard/summary`, `/api/demand`, `/api/backlog`, `/api/spending/*`, `/api/reports/*`
- Filter permutations: single filter, combined filters, `all` sentinel value, unknown values
- Data type and shape validation for all response fields
- Business logic: order total calculation, quarter date ranges, cross-endpoint consistency
- Error paths: 404 for unknown IDs, empty list for unknown filter values

**What is NOT covered:**
- Frontend Vue components — zero test coverage
- `server/mock_data.py` data loading logic
- `server/generate_data.py`
- Mutation endpoints (POST/PATCH/DELETE for tasks, purchase orders) — coverage unclear

## Running Tests

```bash
# From the project root (tests/ directory is at root)
cd server
uv run pytest ../tests/backend/ -v

# With coverage
uv run pytest ../tests/backend/ -v --cov=. --cov-report=term-missing

# Run a specific file
uv run pytest ../tests/backend/test_orders.py -v

# Run a specific test
uv run pytest ../tests/backend/test_orders.py::TestOrdersEndpoints::test_get_all_orders -v
```

The `uv run` prefix is required because the project uses `uv` for Python environment management (no activate script needed).

## CI Integration

CI is defined in `.github/workflows/ci.yml` and runs on push to `main`, `feature/**`, `fix/**` branches and on PRs to `main`.

**Three jobs run in parallel:**

1. **`backend-tests`** (matrix: Python 3.11 and 3.12)
   - Installs dependencies with `uv sync --dev`
   - Runs: `uv run pytest ../tests/backend/ -v --tb=short --strict-markers --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=70`
   - Uploads `tests/coverage.xml` as artifact (7-day retention)
   - Uses `fail-fast: false` so both Python versions always run

2. **`lint`**
   - Runs `ruff check server/ tests/` for linting
   - Runs `ruff format --check server/ tests/` for formatting
   - No auto-fix — must be clean before merging

3. **`frontend-build`**
   - Runs `npm ci && npm run build` in `client/`
   - Uploads `client/dist/` as artifact (7-day retention)
   - Verifies the Vite build does not error — no functional tests

## Testing Gaps

**Frontend has zero test coverage.** No vitest, no jest, no `@vue/test-utils` installed. The `client/package.json` `scripts` block has only `dev`, `build`, and `preview`. All frontend validation in CI is a build check only.

**No e2e tests.** No Playwright, Cypress, or similar framework is configured, despite CLAUDE.md mentioning Playwright MCP tools for manual browser testing during development.

**Mutation endpoints undertested.** POST `/api/tasks`, PATCH `/api/tasks/:id`, DELETE `/api/tasks/:id`, and POST `/api/purchase-orders` are not confirmed to have dedicated tests based on file review.

**No load or performance tests.** The system uses in-memory data, so this is expected for a demo, but there are no benchmarks.

**Filter edge cases for reports endpoints** (`/api/reports/quarterly`, `/api/reports/monthly-trends`) may be covered in `test_reports.py` but that file was not fully reviewed — confirm coverage there independently.

---

*Testing analysis: 2026-06-23*
