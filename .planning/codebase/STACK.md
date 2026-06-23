# Technology Stack

**Analysis Date:** 2026-06-23

## Frontend

**Framework:** Vue 3 (`^3.4.21`) using Composition API (`setup()` pattern, no `<script setup>`)

**Key Libraries:**
- `vue-router` `^4.3.0` — client-side routing
- `axios` `^1.6.7` — HTTP client for API calls (all calls centralized in `client/src/api.js`)

**Build Tool:** Vite `^5.2.0` with `@vitejs/plugin-vue` `^5.0.4`
- Config: `client/vite.config.js`
- Dev server: port 3000
- Module type: ESM (`"type": "module"` in `client/package.json`)

**No TypeScript** — plain JavaScript throughout the frontend.

**No CSS framework** — custom CSS with design tokens (CSS variables), scoped component styles. Color palette: slate/gray (`#0f172a`, `#64748b`, `#e2e8f0`). No emojis in UI.

**Charts:** Custom SVG and CSS Grid — no chart library dependency.

**State Management:** No Vuex/Pinia — shared state via composables in `client/src/composables/`. Global filter state lives in composables as module-level `ref()` instances.

**Localization:** Locale files present at `client/src/locales/` — no i18n library detected in `package.json`.

## Backend

**Language:** Python `>=3.11` (tested on 3.11 and 3.12 in CI)

**Framework:** FastAPI `>=0.110.0`
- ASGI server: Uvicorn `>=0.24.0`
- Entry point: `server/main.py`
- Runs on port 8001
- Interactive docs auto-generated at `http://localhost:8001/docs`

**Validation:** Pydantic `>=2.5.0` — all request/response models defined with `BaseModel`

**Data storage:** In-memory only. JSON files in `server/data/` loaded at startup via `server/mock_data.py`. No persistence between restarts.

**CORS:** Wildcard (`allow_origins=["*"]`) — development configuration only.

## Data Layer

**No database.** All data is static JSON loaded into memory at server startup.

**Data files** (`server/data/`):
- `inventory.json`
- `orders.json`
- `backlog_items.json`
- `demand_forecasts.json`
- `purchase_orders.json`
- `spending.json`
- `transactions.json`

**Data loader:** `server/mock_data.py` — reads and parses JSON files into Python dicts on startup.

## Dev Tooling

**Python package manager:** `uv` (Astral) — lockfile at `server/uv.lock`, config in `server/pyproject.toml`
- Dev dependencies managed under `[tool.uv] dev-dependencies`
- Run commands: `uv run python main.py`, `uv sync --dev`

**Node package manager:** npm — lockfile `client/package-lock.json`

**Python linter/formatter:** `ruff` (installed as a uv tool in CI — not in pyproject.toml devDeps, so install separately with `uv tool install ruff`)
- Checks both `server/` and `tests/` directories

**No frontend linter or formatter** configured (no `.eslintrc`, `.prettierrc`, or `biome.json` detected).

**Testing:**
- Backend: `pytest >=8.0.0` + `pytest-asyncio >=0.23.0` + `httpx >=0.27.0` (for `TestClient`) + `pytest-cov >=4.1.0`
- Test location: `tests/backend/` (outside `server/`)
- Conftest: `tests/backend/conftest.py` adds `server/` to `sys.path`
- No frontend testing framework configured

## Build & Deploy

**CI/CD:** GitHub Actions — `.github/workflows/ci.yml`

Three parallel jobs:
1. **`backend-tests`** — matrix across Python 3.11 and 3.12, runs `pytest` with `--cov-fail-under=70`, uploads `tests/coverage.xml` artifact
2. **`lint`** — installs `ruff`, checks `server/` and `tests/` for lint and format compliance
3. **`frontend-build`** — Node.js 20, runs `npm ci` + `vite build`, uploads `client/dist/` artifact

**Triggers:** push to `main`, `feature/**`, `fix/**`; pull requests to `main`.

**No deployment target configured** — CI only validates build and tests. No Dockerfile, no cloud deployment config.

**Frontend production build command:** `npm run build` (Vite output to `client/dist/`)
**Backend start command:** `uv run python main.py` (from `server/` directory)

## Key Dependencies

| Package | Version | Why it matters |
|---------|---------|----------------|
| `vue` | `^3.4.21` | Core UI framework |
| `vue-router` | `^4.3.0` | SPA routing |
| `axios` | `^1.6.7` | HTTP requests to backend |
| `vite` | `^5.2.0` | Dev server and production bundler |
| `fastapi` | `>=0.110.0` | REST API framework with auto-docs |
| `pydantic` | `>=2.5.0` | Request/response validation (v2 API) |
| `uvicorn` | `>=0.24.0` | ASGI server for FastAPI |
| `pytest` | `>=8.0.0` | Backend test runner |
| `httpx` | `>=0.27.0` | Required by FastAPI `TestClient` |
| `pytest-cov` | `>=4.1.0` | Coverage reporting (70% minimum enforced in CI) |

---

*Stack analysis: 2026-06-23*
