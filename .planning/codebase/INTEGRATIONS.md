# Integrations

**Analysis Date:** 2026-06-23

## External APIs

**None.** This is a self-contained demo application. No third-party APIs are consumed (no Stripe, no Twilio, no external data providers, etc.).

## Authentication

**None.** The application has no authentication layer. All API endpoints are publicly accessible with no authorization checks. The backend CLAUDE.md notes this is intentional for demo purposes only and recommends adding auth before any production use.

## Infrastructure Services

**No external infrastructure services.**

- **Database:** None — data is stored in JSON files (`server/data/*.json`) and loaded into Python memory at startup via `server/mock_data.py`. All filtering and aggregation happen in-process.
- **Cache:** None.
- **Queue/Message broker:** None.
- **File storage:** None — no file uploads or blob storage.
- **Email/SMS:** None.
- **Search:** None.

## Internal Service Boundaries

**Frontend → Backend (HTTP/REST):**

The frontend communicates with the backend exclusively via REST API calls using `axios`. All API calls are centralized in `client/src/api.js`.

- **Base URL:** `http://localhost:8001/api` (hardcoded string in `client/src/api.js` line 3)
- **Protocol:** HTTP (no WebSockets, no GraphQL, no gRPC)
- **Auth header:** None
- **CORS:** Backend allows all origins (`*`) in development

**API surface consumed by the frontend:**

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/inventory` | Filters: `warehouse`, `category` |
| GET | `/api/inventory/:id` | Single item lookup |
| GET | `/api/orders` | Filters: `warehouse`, `category`, `status`, `month` |
| GET | `/api/orders/:id` | Single order lookup |
| GET | `/api/dashboard/summary` | All 4 filters |
| GET | `/api/demand` | No filters |
| GET | `/api/backlog` | No filters |
| GET | `/api/spending/summary` | No filters |
| GET | `/api/spending/monthly` | No filters |
| GET | `/api/spending/categories` | No filters |
| GET | `/api/spending/transactions` | No filters |
| GET | `/api/tasks` | No filters |
| POST | `/api/tasks` | Create task |
| DELETE | `/api/tasks/:id` | Delete task |
| PATCH | `/api/tasks/:id` | Toggle task |
| POST | `/api/purchase-orders` | Create purchase order |
| GET | `/api/purchase-orders/:backlogItemId` | Lookup by backlog item |
| GET | `/api/reports/quarterly` | Filters: `warehouse`, `category` |
| GET | `/api/reports/monthly-trends` | Filters: `warehouse`, `category` |

**Filter query parameters** are appended as URL search params; the value `'all'` is treated as "no filter" and omitted from the request.

## Environment Variables

**No environment variables are required** to run this application in development. The API base URL is hardcoded in `client/src/api.js`. An `.env.example` file exists at the project root but its contents are not readable (permissions restricted). No `dotenv` or `python-dotenv` dependency is present in either `package.json` or `pyproject.toml`.

If the application is extended to use real infrastructure, the following would be candidates for environment variables:
- `VITE_API_BASE_URL` — to make the frontend API base URL configurable
- `CORS_ORIGINS` — to restrict CORS from wildcard to specific domains
- Database connection string (if a database is added)

## CI/CD Integrations

**GitHub Actions** — `.github/workflows/ci.yml`

- Uses `astral-sh/setup-uv@v4` (Astral's official uv action) for Python dependency management
- Uses `actions/setup-node@v4` with npm cache keyed to `client/package-lock.json`
- Uses `actions/checkout@v4` and `actions/upload-artifact@v4`
- Coverage artifact (`tests/coverage.xml`) uploaded per Python version, retained 7 days
- Frontend dist artifact (`client/dist/`) uploaded, retained 7 days
- No deployment step — CI validates only; no integration with Vercel, AWS, Render, Heroku, etc.

---

*Integration audit: 2026-06-23*
