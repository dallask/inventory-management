# Concerns & Technical Debt

**Analysis Date:** 2026-06-23

---

## Critical Issues

### Tasks API endpoints are called but do not exist in the backend

`client/src/App.vue` (lines 92–141) calls `api.getTasks()`, `api.createTask()`, `api.deleteTask()`, and `api.toggleTask()`. These map to `/api/tasks` endpoints defined in `client/src/api.js` (lines 77–95). However, `server/main.py` has no `/api/tasks` route at all. Every page load fires `loadTasks()` on `onMounted`, which will silently fail with a network error (caught and swallowed by `console.error`). Task state is therefore always sourced from the hardcoded mock in `client/src/composables/useAuth.js`, never from the API.

**Files:** `client/src/App.vue`, `client/src/api.js` (lines 77–95), `server/main.py`
**Impact:** Any real task creation/deletion/toggle appears to work locally (mock state mutates) but is never persisted. Adding a task via the UI survives only until page refresh.

### Purchase orders API endpoints called but do not exist in the backend

`client/src/api.js` (lines 97–105) defines `createPurchaseOrder()` and `getPurchaseOrderByBacklogItem()`. These call `POST /api/purchase-orders` and `GET /api/purchase-orders/{backlogItemId}`. `server/main.py` has no such routes. The data (`purchase_orders.json`) is loaded in `server/mock_data.py` and used only to compute the `has_purchase_order` flag in `GET /api/backlog`. Creating a purchase order from the UI will throw a 404/405 error at runtime.

**Files:** `client/src/api.js` (lines 97–105), `server/main.py`, `client/src/views/Backlog.vue`

---

## Technical Debt

### `Dashboard.vue` is a 1,274-line monolith

`client/src/views/Dashboard.vue` is 1,274 lines — more than 3x any other view. It contains all chart rendering, all data fetching, all computed transformations, and all template markup in a single file. The `CLAUDE.md` client guide specifies extracting components when a template exceeds 100 lines and logic exceeds 150 lines. This file violates both thresholds by a large margin.

**Files:** `client/src/views/Dashboard.vue`
**Fix approach:** Extract chart SVGs into reusable components under `client/src/components/`, extract data transformation into a `useDashboard.js` composable.

### `Spending.vue` is 854 lines — same problem at smaller scale

`client/src/views/Spending.vue` (854 lines) duplicates the monolith pattern.

**Files:** `client/src/views/Spending.vue`

### Quarterly report logic duplicated between frontend and backend

`server/main.py` (lines 243–251) re-implements quarter detection with a chain of `if/elif` string-match conditions. The same `QUARTER_MAP` dict exists on line 10–15. The quarter logic is already correct in `QUARTER_MAP`; the `get_quarterly_reports` function re-invents it unnecessarily.

**Files:** `server/main.py` (lines 10–15, 243–251)
**Fix approach:** Replace the elif chain in `get_quarterly_reports` with a loop over `QUARTER_MAP` entries.

### Mock user data hardcoded with real-looking PII in composable

`client/src/composables/useAuth.js` (lines 5–10) contains a hardcoded email (`john.doe@catalystcomponents.com`) and phone number (`+1 (111) 111-1111`). While this is a demo, the pattern embeds identity data in source code, which is hard to locate and replace when moving to real auth.

**Files:** `client/src/composables/useAuth.js`

### `isAuthenticated` is always `true` with no enforcement

`useAuth.js` line 92: `const isAuthenticated = ref(true)`. No route guard or middleware checks this value. The logout handler (line 94–98) calls `alert()` and does nothing else. `isAuthenticated` can never become `false` through any UI action, making the field dead code.

**Files:** `client/src/composables/useAuth.js` (lines 92–98)

### Tasks in `useAuth.js` are mutated directly from `App.vue`

`App.vue` line 114: `currentUser.value.tasks.splice(index, 1)` mutates a property of a `computed()` value. This is a Vue anti-pattern (mutating computed output). The `CLAUDE.md` client guide explicitly warns against this pattern (line: "Never mutate computed properties"). It works only because `currentUser` is a computed that returns an object whose internal properties are not themselves reactive — the mutation silently succeeds but bypasses reactivity.

**Files:** `client/src/App.vue` (lines 113–116), `client/src/composables/useAuth.js` (lines 16–87)

### `v-for` with index key in `Orders.vue`

`client/src/views/Orders.vue` line 87: `v-for="(item, idx) in order.items" :key="idx"`. The `CLAUDE.md` client guide and codebase conventions both flag index-as-key as an anti-pattern. Each order item is a `dict` with no guaranteed unique ID field in the data model.

**Files:** `client/src/views/Orders.vue` (line 87)

---

## Security Concerns

### CORS wildcard (`allow_origins=["*"]`) with `allow_credentials=True`

`server/main.py` lines 51–55: The CORS configuration sets both `allow_origins=["*"]` and `allow_credentials=True`. This is an invalid combination per the CORS spec — browsers block credentialed requests to wildcard origins. More importantly, this is explicitly flagged in `server/CLAUDE.md` as a production risk ("Never use wildcard (*) in production"). There is no environment-based switching — it is always the wildcard.

**Files:** `server/main.py` (lines 50–56)
**Impact:** Would be a misconfigured CORS policy in any deployment beyond local dev.

### Hardcoded API base URL with no environment variable fallback

`client/src/api.js` line 3: `const API_BASE_URL = 'http://localhost:8001/api'`. There is no `VITE_API_BASE_URL` env var or equivalent. Deploying the frontend to any non-localhost target requires a source code change.

**Files:** `client/src/api.js` (line 3)

### No authentication on any API endpoint

`server/main.py` has no middleware or dependency that enforces authentication. Any request to any endpoint succeeds. The `server/CLAUDE.md` acknowledges this explicitly under "Security Notes." For a demo this is acceptable, but it means there is no scaffold in place to add auth later.

### No input length or content validation on string filter parameters

`server/main.py` `apply_filters()` (lines 33–47) passes `warehouse`, `category`, and `status` directly into string comparisons with `.lower()`. No max-length check, no allowlist validation. A client can send arbitrarily long strings. Low risk with in-memory data but worth noting.

**Files:** `server/main.py` (lines 33–47)

---

## Performance Concerns

### All data loaded into memory at startup — no pagination

`server/mock_data.py` loads all JSON files at import time. All filtering in `apply_filters()` and `filter_by_month()` is O(n) list comprehension over the full dataset on every request. With the current dataset sizes (tens of records) this is fine, but there is no pagination for `GET /api/orders` or `GET /api/inventory`. Returning 10,000 orders would return all 10,000 in one response.

**Files:** `server/main.py`, `server/mock_data.py`

### `GET /api/backlog` constructs an O(n*m) cross-product check

`server/main.py` lines 175–180: For each backlog item, it calls `any(po["backlog_item_id"] == item["id"] for po in purchase_orders)`. This is O(backlog_items × purchase_orders) on every request. No indexing.

**Files:** `server/main.py` (lines 174–181)

### No debounce on filter changes that trigger API calls

Filter changes in the composable trigger `watch` callbacks in each view that call the API immediately. With rapid filter changes (e.g., typing), each keystroke fires a new request. No debounce or cancellation of in-flight requests.

**Files:** `client/src/composables/useFilters.js`, view files that watch filter state

### `Dashboard.vue` re-computes all chart data on every filter change

Because all chart computations live in a single component's setup function, a single filter change triggers recomputation of all charts simultaneously. No lazy loading or deferred rendering.

**Files:** `client/src/views/Dashboard.vue`

---

## Inconsistencies

### Filter state naming mismatch: `selectedLocation` vs `warehouse`

`useFilters.js` uses `selectedLocation` as the ref name, but maps it to `warehouse` in `getCurrentFilters()`. Views receive `selectedLocation` from the composable but must know it maps to `warehouse` in the API. This causes confusion: some views destructure `selectedLocation`, others call `getCurrentFilters()` and use `warehouse`.

**Files:** `client/src/composables/useFilters.js` (lines 7, 34)

### `Spending.vue` does not use `getCurrentFilters()` for all calls

`client/src/views/Spending.vue` uses `selectedPeriod` from `useFilters` but the spending endpoints (`/api/spending/*`) accept no filter parameters. The period filter is extracted but never passed to any spending API call, creating a silent filter mismatch where the UI shows "filtered" state but spending data is always unfiltered.

**Files:** `client/src/views/Spending.vue`, `server/main.py` (lines 211–229)

### `console.log('Transaction clicked:', transaction)` left in production code

`client/src/views/Spending.vue` line 451: debug console.log left in production component.

**Files:** `client/src/views/Spending.vue` (line 451)

### Error styling defined twice in `Inventory.vue`

`client/src/views/Inventory.vue` lines 321 and 327 both define `.error {}` in scoped styles, causing a duplicate CSS rule.

**Files:** `client/src/views/Inventory.vue` (lines 321, 327)

### No Vue Router route guards despite `isAuthenticated` existing

Vue Router is configured in the project (`vue-router` is a dependency) but no navigation guards exist. The `isAuthenticated` ref in `useAuth.js` exists but is never used by the router. If auth were added, there is no infrastructure to redirect unauthenticated users.

---

## Missing Pieces

### No frontend test coverage whatsoever

No `*.test.*` or `*.spec.*` files exist anywhere under `client/`. Backend has 5 test files under `tests/backend/`. There is zero frontend test coverage for Vue components, composables, or the `api.js` client.

**Files:** `client/` (entire directory)

### No error boundary or global error handler

There is no Vue `errorCaptured` hook, no global `app.config.errorHandler`, and no error boundary component. An unhandled error in any child component will propagate silently or crash the component subtree with no user-visible feedback.

### No loading skeleton or optimistic UI for initial page load

Each view shows a blank state while `loading = true`. There are no skeleton screens or placeholder content. On slow connections the user sees empty pages briefly for every navigation.

### No `.env` support for environment-specific configuration

There is no `.env.example`, no `VITE_*` variables, and no documentation about environment configuration. Deploying requires source edits.

### No pagination controls in any list view

Inventory, Orders, Backlog, and Demand views render all records returned from the API in a single table/list with no pagination, virtual scrolling, or "load more" pattern.

### No route-level code splitting

`client/src/main.js` (assumed) imports all views statically. No `defineAsyncComponent()` or dynamic `import()` is used. The entire application ships as a single bundle regardless of which view the user visits.

---

## Dependency Risks

### No lock file version pinning for Python dependencies

`server/requirements.txt` uses `>=` ranges only: `fastapi>=0.110.0`, `uvicorn>=0.24.0`, `pydantic>=2.5.0`. This means `uv` or pip will pull the latest compatible versions. A breaking change in any package (e.g., Pydantic v3 when released) could silently break the server.

**Files:** `server/requirements.txt`
**Fix approach:** Pin to exact versions (`==`) or use `uv.lock` for reproducible installs.

### No lockfile committed for backend (no `uv.lock` in repo)

The `uv` tool generates a `uv.lock` file for reproducible installs, but it does not appear to be committed. Without it, different environments may resolve different dependency versions.

### Frontend dependencies are current but not pinned to exact versions

`client/package.json` uses `^` ranges (e.g., `"vue": "^3.4.21"`). A patch bump that introduces a regression would be auto-installed by `npm install`. No `package-lock.json` committed status is known — if absent, npm would resolve fresh.

**Files:** `client/package.json`

---

## Scalability Limits

### In-memory data store — no persistence across server restarts

All data lives in Python variables loaded from JSON at startup. Any state mutations (purchase orders created, tasks added) exist only in memory and are lost on server restart. The `server/CLAUDE.md` notes this explicitly. This is the primary scalability wall: the system cannot persist user actions and cannot scale to multiple server instances.

**Files:** `server/mock_data.py`, `server/main.py`

### Global filter state is a module-level singleton

`useFilters.js` (lines 4–7) declares `selectedPeriod`, `selectedLocation`, `selectedCategory`, and `selectedStatus` as module-level `ref`s outside any function. This is the standard Vue composable singleton pattern and works correctly for a single-user SPA. If the app ever moved to SSR (e.g., Nuxt), these singletons would be shared across user sessions — a critical SSR leak.

**Files:** `client/src/composables/useFilters.js` (lines 4–7)

### No rate limiting on any API endpoint

`server/main.py` has no rate limiting middleware. A client could hammer any endpoint without restriction. Combined with the O(n) filtering on every request, a large dataset + high request rate would saturate the server.

### Quarter filter hardcoded to year 2025

`server/main.py` lines 10–15: `QUARTER_MAP` only covers 2025 quarters. Orders outside 2025 are silently excluded from quarter-filtered results. Adding 2026 data requires a code change.

**Files:** `server/main.py` (lines 10–15)

---

*Concerns audit: 2026-06-23*
