<!-- refreshed: 2026-06-23 -->
# Architecture

**Analysis Date:** 2026-06-23

## System Overview

The Factory Inventory Management System is a full-stack SPA (Single Page Application) with a clear client/server separation. The Vue 3 frontend communicates with a Python FastAPI backend over HTTP. All backend data lives in in-memory Python lists loaded at startup from JSON files in `server/data/` — there is no database. Filtering happens on the server side at query time by iterating over these in-memory collections.

The frontend is a dashboard-style SaaS application organized around a persistent shell (sidebar + topbar + filter bar) with page-level views swapped in via Vue Router. Global filter state is held in a singleton composable (`useFilters`) that all views read at data-load time; there is no Vuex/Pinia store.

## Architectural Pattern

**Overall:** Layered Client/Server with In-Memory Data Store

- **Presentation layer:** Vue 3 SPA (`client/src/views/`, `client/src/components/`)
- **API client layer:** Centralized Axios wrapper (`client/src/api.js`)
- **HTTP transport:** REST over localhost (port 3000 → 8001)
- **API layer:** FastAPI route handlers (`server/main.py`)
- **Business logic layer:** Inline filter/aggregation functions in `server/main.py`
- **Data layer:** JSON files at startup → Python module-level lists (`server/mock_data.py`)

There is no ORM, no migrations, and no persistence — writes (purchase orders, tasks) mutate in-memory lists only and are lost on server restart.

## Data Flow

### Read Request (most endpoints)

1. User selects a filter in `client/src/components/FilterBar.vue`
2. `FilterBar` updates the singleton refs in `client/src/composables/useFilters.js`
3. The active view's `watch` on filter state calls `getCurrentFilters()` from `useFilters`
4. The view calls the relevant method on `client/src/api.js`, which builds `URLSearchParams` and fires an Axios GET to `http://localhost:8001/api/...`
5. FastAPI receives the request in a route handler in `server/main.py`
6. Handler calls `apply_filters()` and/or `filter_by_month()` helper functions, which iterate the in-memory lists loaded by `server/mock_data.py`
7. FastAPI serializes the filtered Python dicts through a Pydantic `response_model` and returns JSON
8. The view stores the result in a `ref`, and `computed` properties derive display-ready values

### Write Request (purchase orders, tasks)

1. User action in a view/modal calls an API write method (e.g., `api.createPurchaseOrder(...)`)
2. Axios fires a POST to FastAPI
3. FastAPI validates the body with a Pydantic request model and appends the new record to the in-memory list
4. The view updates local state with the returned object

## Key Abstractions

**`useFilters` composable** (`client/src/composables/useFilters.js`):
- Singleton module-level refs (`selectedPeriod`, `selectedLocation`, `selectedCategory`, `selectedStatus`)
- `getCurrentFilters()` maps UI names to API query param names (`selectedLocation` → `warehouse`, `selectedPeriod` → `month`)
- All views consume this composable; FilterBar writes it; this is the only shared global state

**`api` object** (`client/src/api.js`):
- Single exported object with async methods for every endpoint
- Converts filter objects to `URLSearchParams` before each GET
- All HTTP is centralized here — views never call Axios directly

**Pydantic Models** (`server/main.py`):
- `InventoryItem`, `Order`, `DemandForecast`, `BacklogItem`, `PurchaseOrder`, `CreatePurchaseOrderRequest`
- Used as `response_model` on GET endpoints for automatic serialization and validation
- Request bodies validated via POST body models

**Filter helpers** (`server/main.py`):
- `apply_filters(items, warehouse, category, status)` — reusable across all endpoints
- `filter_by_month(items, month)` — handles both direct month strings (`2025-01`) and quarter strings (`Q1-2025`)

**Mock data module** (`server/mock_data.py`):
- Loads all JSON at Python import time into module-level variables
- Variables are imported directly into `main.py` and used as the source of truth throughout the server's lifetime

## Frontend Architecture

**Shell layout** (`client/src/App.vue`):
- CSS Grid with two columns: `Sidebar` (collapsible) and `.app-main`
- `.app-main` contains `Topbar`, `FilterBar`, and `<router-view />`
- Sidebar collapse state is managed in `App.vue` with `localStorage` persistence and a `1280px` breakpoint override

**Routing** (`client/src/main.js`):
- `vue-router` with `createWebHistory()` (HTML5 pushState)
- 8 routes, each mapping a path to a view component; no lazy loading
- Routes: `/`, `/inventory`, `/orders`, `/demand`, `/spending`, `/reports`, `/restocking`, `/backlog`

**Views** (`client/src/views/`):
- Each view is a self-contained page component
- Pattern: `ref` for raw API data → `computed` for filtered/derived display data → `watch` on filter state to reload
- Loading/error state managed locally per view with `loading` and `error` refs

**Components** (`client/src/components/`):
- `Sidebar.vue` — collapsible vertical nav with icon+label items
- `Topbar.vue` — sticky header strip
- `FilterBar.vue` — 4 dropdowns writing to `useFilters` singleton
- `LanguageSwitcher.vue` — wraps `useI18n` locale toggle
- `ProfileMenu.vue` — avatar + dropdown
- Modal components (`BacklogDetailModal`, `CostDetailModal`, `InventoryDetailModal`, `ProductDetailModal`, `ProfileDetailsModal`, `TasksModal`) — opened via boolean `ref` in parent

**Composables** (`client/src/composables/`):
- `useFilters.js` — global filter state (singleton pattern)
- `useAuth.js` — mock user object (always authenticated, no real auth)
- `useI18n.js` — custom i18n with `en`/`ja` locale files; currency auto-switches with locale
- `useRestockingOrders.js` — local state for the restocking view

**i18n** (`client/src/locales/`):
- `en.js` and `ja.js` — plain JS objects with nested translation keys
- `useI18n` exposes a `t(key)` function; locale stored in `localStorage`

**Design tokens** (`client/src/assets/dallask-tokens.css`):
- CSS custom properties under `--dk-*` namespace
- App-level aliases mapped in `App.vue` `<style>` (e.g., `--surface-1: var(--dk-surface-1)`)
- Global utility classes defined in `App.vue` `<style>` (unscoped): `.card`, `.badge`, `.stat-card`, `.table-container`

## Backend Architecture

**Entry point** (`server/main.py`):
- Single file containing all route definitions, Pydantic models, and helper functions
- FastAPI app instantiated at module level; CORS middleware allows all origins (`*`)
- Server started via `uvicorn` on port `8001`

**Request handling pattern:**
1. Route function receives optional query params as `Optional[str]`
2. Calls `apply_filters()` and/or `filter_by_month()` on the relevant module-level list
3. Returns filtered list (FastAPI serializes via `response_model`)
4. Aggregation endpoints (e.g., `/api/dashboard/summary`, `/api/reports/quarterly`) compute derived values inline before returning a dict

**Data access:**
- All data accessed via module-level variables imported from `mock_data.py`
- No database driver, no ORM, no connection pooling
- `server/data/` contains 7 JSON files: `inventory.json`, `orders.json`, `demand_forecasts.json`, `backlog_items.json`, `purchase_orders.json`, `spending.json`, `transactions.json`

**Write endpoints:**
- `POST /api/purchase-orders` — appends to in-memory `purchase_orders` list
- `POST /api/tasks`, `DELETE /api/tasks/{id}`, `PATCH /api/tasks/{id}` — task CRUD on in-memory list

## Cross-Cutting Concerns

**Authentication:**
- None implemented. `useAuth` returns `isAuthenticated: true` always. The backend has no auth middleware.

**Error handling:**
- Backend: `HTTPException(status_code=404)` for item-not-found lookups; no global error handler
- Frontend: Each view has a local `error` ref populated in `catch` blocks; displayed inline

**Logging:**
- Backend: No structured logging; `print()` statements only (visible in terminal)
- Frontend: `console.error()` in catch blocks; no log aggregation

**CORS:**
- `allow_origins=["*"]` — development only; documented in `server/CLAUDE.md` as requiring restriction for production

**Caching:**
- None. Every API request re-filters the in-memory lists.

**Testing:**
- Backend tests use pytest + FastAPI `TestClient` in `tests/backend/`
- No frontend unit tests detected

---

*Architecture analysis: 2026-06-23*
