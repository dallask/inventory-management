# Coding Conventions

**Analysis Date:** 2026-06-23

## Language Style

**JavaScript (Frontend):**
- ES modules throughout (`"type": "module"` in `client/package.json`)
- Async/await for all API calls — no raw promise chains
- Arrow functions preferred for callbacks and methods
- Template literals used for string interpolation
- No TypeScript — plain `.js` files only
- `const` by default; `let` when reassignment is needed

**Python (Backend):**
- Python 3.11+ with type annotations on function signatures
- `Optional[str]` from `typing` for nullable params
- List comprehensions preferred over loops for data filtering
- `snake_case` for all Python identifiers (variables, functions, parameters)
- Pydantic v1-style `BaseModel` classes for all response shapes
- Module-level imports grouped: stdlib → third-party → local

## Naming Conventions

**JavaScript files:**
- Vue components: `PascalCase.vue` (e.g., `ProductDetailModal.vue`, `FilterBar.vue`)
- Composables: `camelCase.js` prefixed with `use` (e.g., `useFilters.js`, `useI18n.js`)
- Utilities: `camelCase.js` (e.g., `currency.js`)
- Views: `PascalCase.vue` in `client/src/views/` (e.g., `Dashboard.vue`, `Backlog.vue`)

**JavaScript identifiers:**
- Variables and functions: `camelCase` (e.g., `selectedPeriod`, `loadData`, `getCurrentFilters`)
- Component names in `export default`: `PascalCase` matching filename
- Event handlers: `handle` prefix or verb-noun (`handleUpdate`, `showBacklogDetail`, `openPOModal`)
- Boolean refs: `is`/`has`/`show` prefix (e.g., `loading`, `showProductModal`, `hasActiveFilters`)

**Python identifiers:**
- Functions: `snake_case` (e.g., `filter_by_month`, `apply_filters`, `get_inventory`)
- Classes (Pydantic models): `PascalCase` (e.g., `InventoryItem`, `Order`, `DemandForecast`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `QUARTER_MAP`)
- Route params: `snake_case` matching model field names

**API endpoints:**
- Plural nouns with hyphens: `/api/inventory`, `/api/orders`, `/api/demand`, `/api/dashboard/summary`
- Sub-resources: `/api/spending/summary`, `/api/spending/monthly`, `/api/spending/categories`
- Query params: `snake_case` matching Python param names (`warehouse`, `category`, `status`, `month`)

## Component Structure

All Vue components use **Options API with `setup()`** — not `<script setup>`. The pattern observed across all views:

```vue
<template>
  <!-- Declarative HTML — i18n via t('key') helper, no raw strings -->
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import ChildComponent from '../components/ChildComponent.vue'

export default {
  name: 'ComponentName',
  components: { ChildComponent },
  setup() {
    // 1. Composables first
    const { t, currentCurrency } = useI18n()
    const { selectedPeriod, getCurrentFilters } = useFilters()

    // 2. Reactive state
    const loading = ref(true)
    const error = ref(null)
    const data = ref([])

    // 3. Computed properties (derived/cached values)
    const filteredData = computed(() => { /* ... */ })

    // 4. Methods
    const loadData = async () => { /* ... */ }

    // 5. Watchers
    watch([selectedPeriod, selectedLocation], loadData)

    // 6. Lifecycle
    onMounted(() => { loadData() })

    // 7. Return everything used in template
    return { loading, error, data, filteredData, loadData }
  }
}
</script>

<style scoped>
/* Component-scoped styles only */
</style>
```

**Key structural rules:**
- Template section first, then script, then scoped styles
- `<script setup>` is NOT used — always `export default { setup() {} }`
- All state is `ref()` or `computed()`, never plain variables
- Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties
- Components in `client/src/components/` are reusable modals and UI pieces
- Views in `client/src/views/` are page-level route targets

## Error Handling

**Frontend (Vue components):**

Standard three-state pattern used consistently across all views:

```javascript
const loading = ref(true)
const error = ref(null)

const loadData = async () => {
  try {
    loading.value = true
    error.value = null
    data.value = await api.getData(getCurrentFilters())
  } catch (err) {
    error.value = 'Failed to load data'
    console.error('Load error:', err)
  } finally {
    loading.value = false
  }
}
```

Template pattern:
```vue
<div v-if="loading">Loading...</div>
<div v-else-if="error">{{ error }}</div>
<div v-else><!-- actual content --></div>
```

**Backend (FastAPI):**

Use `HTTPException` for all explicit errors:

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
```

- 404 for missing resources (item by ID not found)
- 400 for bad input
- FastAPI handles 422 (Pydantic validation) automatically
- Filter misses return empty list `[]`, not 404

## State Management

**Filter state** is managed as a singleton composable in `client/src/composables/useFilters.js`. Module-level refs are shared across all component instances (no Vuex/Pinia):

```javascript
// Singleton — refs defined at module scope, shared across all callers
const selectedPeriod = ref('all')
const selectedLocation = ref('all')
const selectedCategory = ref('all')
const selectedStatus = ref('all')

export function useFilters() {
  // Returns same refs to every caller
  return { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, ... }
}
```

**Watch pattern** for reactive data reloading:
```javascript
watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)
```

**No global store** (no Vuex, no Pinia) — composables with module-level refs serve this role.

## API Patterns

All API calls are centralized in `client/src/api.js` as a plain object export. No class, no Axios instance configuration beyond base URL.

```javascript
import axios from 'axios'
const API_BASE_URL = 'http://localhost:8001/api'

export const api = {
  async getOrders(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    const response = await axios.get(`${API_BASE_URL}/orders?${params.toString()}`)
    return response.data
  }
}
```

**Rules:**
- Skip appending a param if its value is `'all'` or falsy
- Always return `response.data` (unwrap Axios wrapper)
- No error handling in `api.js` — callers handle errors in try/catch
- Filter params use `URLSearchParams` for safe encoding

## Comments and Documentation

**Python docstrings:**
- Module-level `"""docstring"""` at top of each file
- Function docstrings for utility functions and fixtures: one-line summary style
- No multi-line docstrings with Args/Returns sections — kept brief

**JavaScript comments:**
- Inline `//` comments for section headers and intent (e.g., `// Shared filter state (singleton pattern)`)
- No JSDoc annotations on functions
- Group returns with comments: `// State`, `// Computed`, `// Methods`

**Test files:**
- Module docstring at top of each test file (e.g., `"""Tests for orders API endpoints."""`)
- Every test function has a one-line docstring describing what it validates
- Section comments with `# ── Section Name ──` decorators to group related tests within a class

---

*Convention analysis: 2026-06-23*
