<!-- refreshed: 2026-06-23 -->
# Codebase Structure

**Analysis Date:** 2026-06-23

## Top-Level Layout

```
inventory-management/
├── client/              # Vue 3 SPA (Vite, port 3000)
├── server/              # Python FastAPI backend (port 8001)
├── tests/               # Backend pytest test suite
├── docs/                # Project documentation
├── scripts/             # Utility scripts
├── .claude/             # Claude Code configuration and GSD framework
├── .github/             # CI workflow definitions
├── .planning/           # GSD planning artifacts
├── CLAUDE.md            # Root-level AI instructions
├── README.md            # Project overview
├── .mcp.json            # MCP server configuration
└── .env.example         # Environment variable template (no real values)
```

## Frontend Structure

```
client/
├── index.html                    # Vite HTML entry point
├── package.json                  # npm manifest (vue, vue-router, axios, vite)
├── vite.config.js                # Vite config — sets dev server port to 3000
├── CLAUDE.md                     # Frontend-specific AI instructions
└── src/
    ├── main.js                   # App bootstrap: createApp, createRouter, mount
    ├── App.vue                   # Root shell: Sidebar, Topbar, FilterBar, <router-view>
    ├── api.js                    # Centralized Axios API client (all HTTP here)
    ├── assets/
    │   └── dallask-tokens.css    # Design token CSS custom properties (--dk-* namespace)
    ├── views/                    # Page-level route components (one per route)
    │   ├── Dashboard.vue         # / — KPIs, summary stats
    │   ├── Inventory.vue         # /inventory — inventory table
    │   ├── Orders.vue            # /orders — orders table
    │   ├── Demand.vue            # /demand — demand forecast table
    │   ├── Spending.vue          # /spending — spending breakdown
    │   ├── Reports.vue           # /reports — quarterly + monthly trends
    │   ├── Restocking.vue        # /restocking — restocking orders
    │   └── Backlog.vue           # /backlog — backlog items with purchase orders
    ├── components/               # Reusable UI components
    │   ├── Sidebar.vue           # Collapsible vertical nav
    │   ├── Topbar.vue            # Sticky top header bar
    │   ├── FilterBar.vue         # 4-filter bar (period, location, category, status)
    │   ├── LanguageSwitcher.vue  # EN/JA toggle
    │   ├── ProfileMenu.vue       # Avatar + dropdown menu
    │   ├── BacklogDetailModal.vue
    │   ├── CostDetailModal.vue
    │   ├── InventoryDetailModal.vue
    │   ├── ProductDetailModal.vue
    │   ├── ProfileDetailsModal.vue
    │   └── TasksModal.vue
    ├── composables/              # Shared reactive logic (singleton pattern)
    │   ├── useFilters.js         # Global filter state (selectedPeriod, location, category, status)
    │   ├── useAuth.js            # Mock user object + auth helpers
    │   ├── useI18n.js            # Custom i18n: t() function, locale/currency state
    │   └── useRestockingOrders.js # Local state for restocking view
    ├── locales/                  # Translation files
    │   ├── en.js                 # English strings (nested object)
    │   └── ja.js                 # Japanese strings (nested object)
    └── utils/
        └── currency.js           # Currency formatting helpers
```

## Backend Structure

```
server/
├── main.py              # All FastAPI app code: models, routes, filter helpers
├── mock_data.py         # Loads JSON files into module-level variables at startup
├── pyproject.toml       # Python project config (uv managed)
├── uv.lock              # Dependency lockfile
├── data/                # JSON source data (loaded into memory on startup)
│   ├── inventory.json
│   ├── orders.json
│   ├── demand_forecasts.json
│   ├── backlog_items.json
│   ├── purchase_orders.json
│   ├── spending.json
│   └── transactions.json
├── .venv/               # Python virtual environment (managed by uv, not committed)
└── .pytest_cache/       # pytest artifact cache
```

## Tests Structure

```
tests/
├── pytest.ini           # pytest config
├── README.md
├── TEST_SUMMARY.md
└── backend/             # FastAPI endpoint tests using TestClient
    └── (test_*.py files)
```

## Key Files

A developer needs to know these files to work in this codebase:

| File | Purpose |
|------|---------|
| `client/src/main.js` | Router definition and app bootstrap — add new routes here |
| `client/src/App.vue` | Shell layout and global styles (unscoped CSS for shared utilities) |
| `client/src/api.js` | All HTTP calls — add new API methods here |
| `client/src/composables/useFilters.js` | Global filter state — source of truth for all view data loads |
| `client/src/assets/dallask-tokens.css` | Design token definitions — reference for all colors/spacing |
| `server/main.py` | All backend routes, Pydantic models, filter logic |
| `server/mock_data.py` | Data loading — add new JSON datasets here |
| `server/data/*.json` | Actual data — edit to change seed data |

## Naming Conventions

**Vue files:**
- PascalCase for all `.vue` files: `FilterBar.vue`, `Dashboard.vue`, `TasksModal.vue`
- Views are named for the domain concept (`Orders.vue`, `Backlog.vue`)
- Modals are suffixed `Modal` (`BacklogDetailModal.vue`)
- Layout components are named for their position (`Sidebar.vue`, `Topbar.vue`)

**JavaScript files:**
- `camelCase` for all `.js` files: `api.js`, `useFilters.js`, `currency.js`
- Composables are prefixed `use`: `useFilters.js`, `useAuth.js`, `useI18n.js`
- Locale files named by ISO code: `en.js`, `ja.js`

**Python files:**
- `snake_case`: `main.py`, `mock_data.py`
- Data files: `snake_case` with `.json` extension: `backlog_items.json`, `demand_forecasts.json`

**CSS variables:**
- Design tokens: `--dk-*` namespace (e.g., `--dk-surface-1`, `--dk-primary`)
- App aliases: no namespace (e.g., `--surface-1`, `--border-color`) — defined in `App.vue`

## Where to Add New Code

**New route/page:**
1. Create `client/src/views/NewPage.vue`
2. Add route to the `routes` array in `client/src/main.js`
3. Add nav link to `client/src/components/Sidebar.vue`
4. Add API method(s) to `client/src/api.js`
5. Add backend endpoint(s) to `server/main.py`

**New API endpoint:**
1. Define a Pydantic model in `server/main.py` if new response shape is needed
2. Add `@app.get("/api/...")` route function in `server/main.py`
3. Use `apply_filters()` if the endpoint should respect warehouse/category/status filters
4. Add a corresponding method to the `api` object in `client/src/api.js`
5. Write tests in `tests/backend/`

**New shared data source:**
1. Add a JSON file to `server/data/`
2. Load it in `server/mock_data.py` via `load_json_file()`
3. Import the new variable in `server/main.py`

**New shared frontend logic:**
- Create a composable in `client/src/composables/useMyFeature.js`
- Use the singleton pattern (module-level refs outside the export function) only if global state is needed

**New component:**
- Place in `client/src/components/` if reusable across views
- Place inline in the view file if used only once in that view

---

*Structure analysis: 2026-06-23*
