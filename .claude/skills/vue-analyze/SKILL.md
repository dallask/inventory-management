---
name: vue-analyze
description: >
  Analyzes Vue 3 component structure and suggests concrete optimizations for
  performance and code reuse. Invoke when the user asks to "analyze", "audit",
  "optimize", or "refactor" a Vue component or the frontend codebase.
  Also invoke proactively before implementing a feature in a file > 300 lines.
---

# Vue Component Analysis Skill

## When to invoke
- User asks to "analyze", "audit", "optimize", or "review" a Vue component
- User asks "what can I refactor?" or "is this component too big?"
- A file you're about to modify is > 300 lines
- User asks why re-renders are slow, or why data loads twice

## How to run an analysis

### Step 1 — Gather scope

If the user didn't name a specific file, identify candidates:
```bash
wc -l client/src/views/*.vue client/src/components/*.vue | sort -rn | head -15
```
Files > 300 lines are primary candidates. Under 100 lines rarely need optimization.

### Step 2 — Run the 7 checks below on each target file

### Step 3 — Produce a prioritized findings table

| Priority | Check | Finding | File:Line | Fix |
|----------|-------|---------|-----------|-----|
| P1 | heavy-method | `formatRows()` called in template expression | Dashboard.vue:145 | Move to `computed` |
| P2 | split-component | View is 1271 lines, 3 distinct sections | Dashboard.vue | Extract 2 sub-components |

### Step 4 — Apply fixes

Per CLAUDE.md: **delegate all `.vue` file edits to the `vue-expert` agent.** Write a precise brief for each fix (what line to change, exact before/after) — don't leave it open-ended.

---

## The 7 Checks

### Check 1 — Method vs computed misuse (Performance — P1)

**What to look for:**
- Method calls in template that derive data from refs (`v-for="item in getFilteredItems()"`, `{{ formatSummary() }}`)
- Computed properties that have side effects (`someComputed.value = api.getData()`)
- Watchers that re-derive data that could be a computed

**Grep:**
```bash
grep -n "v-for.*()\"" <file>          # methods called in v-for
grep -n "{{ .*() }}" <file>           # methods in interpolation
grep -n "watch.*=>" <file>            # see if watcher rebuilds data
```

**Bad → Good:**
```js
// ❌ Recalculates every render
const getFilteredOrders = () => orders.value.filter(o => o.status === selectedStatus.value)
// template: v-for="order in getFilteredOrders()"

// ✅ Cached until orders or selectedStatus changes
const filteredOrders = computed(() =>
  orders.value.filter(o => o.status === selectedStatus.value)
)
// template: v-for="order in filteredOrders"
```

---

### Check 2 — Watch vs computed confusion (Performance — P1)

**What to look for:**
- `watch` that sets a ref to a value derived from other refs — this is always a computed
- `watchEffect` used where a `watch` with specific sources is more correct
- Watches that trigger API calls that could instead be driven by computed params + a single watch

**Grep:**
```bash
grep -n -A 5 "watch(\[" <file>        # multi-source watches
grep -n "watch.*=>" <file>
```

**Bad → Good:**
```js
// ❌ Watch rebuilding derived data
watch([orders, selectedStatus], () => {
  filteredOrders.value = orders.value.filter(o => o.status === selectedStatus.value)
})

// ✅ Computed (cached, no side effect)
const filteredOrders = computed(() =>
  orders.value.filter(o => o.status === selectedStatus.value)
)
```

**Correct watch pattern** — only use watch when you need a side effect:
```js
// ✅ Watch to trigger API call when filters change
const apiParams = computed(() => ({
  warehouse: selectedLocation.value,
  category: selectedCategory.value,
  status: selectedStatus.value,
  month: selectedPeriod.value,
}))

watch(apiParams, loadData, { deep: true })
onMounted(loadData)
```

---

### Check 3 — Repeated loading boilerplate (Reuse — P2)

**What to look for:**
- Multiple views each defining their own `loading`, `error`, `data` refs
- The same try/catch/finally/onMounted pattern copy-pasted across files

**Grep:**
```bash
grep -rn "const loading = ref" client/src/views/
grep -rn "const error = ref" client/src/views/
grep -rn "onMounted.*load" client/src/views/
```

**Pattern to extract into a composable:**
```js
// ❌ In every view
const loading = ref(false)
const error = ref(null)
const data = ref([])
const loadData = async () => {
  try {
    loading.value = true
    error.value = null
    data.value = await api.getData(getCurrentFilters())
  } catch (err) {
    error.value = 'Failed to load data'
  } finally {
    loading.value = false
  }
}
onMounted(loadData)
watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)

// ✅ Extract to composables/useAsyncData.js
export function useAsyncData(fetcher) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const load = async () => {
    try {
      loading.value = true
      error.value = null
      data.value = await fetcher()
    } catch (err) {
      error.value = err.message || 'Failed to load'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}

// In a view:
const { data: orders, loading, error, load } = useAsyncData(
  () => api.getOrders(getCurrentFilters())
)
onMounted(load)
watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], load)
```

---

### Check 4 — Component size and split candidates (Reuse — P2)

**Thresholds:**
| Lines | Action |
|-------|--------|
| < 150 | No split needed |
| 150–300 | Watch — split if template has 2+ distinct sections |
| 300–600 | Split: extract at least one sub-component |
| > 600 | Split: extract 2–3 sub-components and/or a composable |

**How to identify split points:**

```bash
# Count template vs script vs style lines
awk '/<template>/,/<\/template>/' <file> | wc -l
awk '/<script>/,/<\/script>/' <file> | wc -l
```

Look for:
- Template sections separated by comments (`<!-- KPI Section -->`, `<!-- Chart Section -->`)
- Groups of computed properties that only serve one template region
- Modals defined inline that are already large (`> 80 lines`)

**Naming convention for extracted components:**
- `ViewNameSection.vue` for sub-sections (e.g., `DashboardKpiGrid.vue`, `DashboardOrderHealth.vue`)
- `use<Feature>.js` for extracted composable logic

---

### Check 5 — v-for key quality (Correctness/Performance — P1)

**What to look for:**
- `v-for` using array index as key
- `v-for` with no key at all
- `v-for` on a complex object where key is a non-unique field

**Grep:**
```bash
grep -n "v-for" <file>
grep -n ":key=\"index\"" <file>
grep -n "key=\"index\"" <file>
```

**Bad → Good:**
```html
<!-- ❌ Index key — Vue reuses wrong DOM nodes when list reorders -->
<div v-for="(item, index) in items" :key="index">

<!-- ✅ Stable unique ID -->
<div v-for="item in items" :key="item.id">
<div v-for="item in items" :key="item.sku">
<div v-for="row in monthlyData" :key="row.month">
```

---

### Check 6 — v-if vs v-show misuse (Performance — P2)

**Rule:**
- `v-if` = DOM removed entirely. Use for content that's rarely shown or conditionally invalid.
- `v-show` = CSS `display: none`. Use for content toggled frequently (tabs, accordions, dropdowns).

**What to look for:**
- `v-if` on loading spinners or error messages (toggled constantly → prefer `v-show`)
- `v-show` on content gated by auth/permissions (should be `v-if` — wrong users shouldn't get the DOM)
- `v-if` inside tight `v-for` loops (Vue evaluates it per item per render)

**Grep:**
```bash
grep -n "v-if=\"loading\"\|v-if=\"error\"" <file>
```

---

### Check 7 — Missing cleanup (Correctness — P1)

**What to look for:**
- `addEventListener` in `onMounted` without a matching `removeEventListener` in `onUnmounted`
- `setInterval` / `setTimeout` without `clearInterval` / `clearTimeout`
- Subscriptions, observers, or timers started in `setup()` or `onMounted` that never stop

**Grep:**
```bash
grep -n "addEventListener\|setInterval\|setTimeout" <file>
grep -n "onUnmounted" <file>
```

**Bad → Good:**
```js
// ❌ Leaks listener on every component mount
onMounted(() => {
  window.addEventListener('resize', onResize)
})

// ✅ Cleaned up
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
```

---

## Priority guide

| Priority | Meaning | Fix when |
|----------|---------|----------|
| **P1** | Causes bugs or measurable perf regression | Before merging |
| **P2** | Increases maintenance cost, harms readability | This sprint |
| **P3** | Nice-to-have polish | When touching the file anyway |

---

## Known findings in this codebase

Run these to get a fast baseline before starting a full analysis:

```bash
# Large files (>300 lines)
wc -l client/src/views/*.vue client/src/components/*.vue | awk '$1 > 300' | sort -rn

# Index keys in v-for
grep -rn ":key=\"index\"" client/src/

# Missing onUnmounted cleanup
grep -rn "addEventListener" client/src/ --include="*.vue" | grep -v "onUnmounted"

# Methods called in templates (potential computed candidates)
grep -rn "{{ .*() }}\|v-for=\".*()\"" client/src/views/

# Repeated loading boilerplate
grep -rn "const loading = ref(false)" client/src/views/

# watch rebuilding derived data (pattern: watch → .value =)
grep -rn -A 3 "watch(" client/src/views/ | grep -B 1 "\.value ="
```

### Pre-identified high-value targets

| File | Lines | Top finding |
|------|-------|-------------|
| `views/Dashboard.vue` | 1271 | Split into 3–4 sub-components; extract `useDashboard` composable |
| `views/Spending.vue` | 852 | Extract chart logic into `useSpendingCharts` composable |
| `views/Reports.vue` | 488 | Extract quarterly/monthly sections into sub-components |
| `components/TasksModal.vue` | 621 | Extract task list item into `TaskItem.vue` |

---

## Output format

Always produce findings in this structure before proposing fixes:

```
## Analysis: <filename>

**Size:** N lines (template: X, script: Y, style: Z)

### Findings

| # | Priority | Check | Location | Description |
|---|----------|-------|----------|-------------|
| 1 | P1 | method-vs-computed | line 145 | `formatRows()` called in v-for expression |
| 2 | P2 | component-split | lines 1–400 | KPI section (lines 10–180) and chart section (lines 181–400) are independent — extract `DashboardKpiGrid.vue` |
| 3 | P2 | repeated-loader | lines 300–330 | Same try/catch/finally/loading pattern as Orders.vue and Inventory.vue |

### Recommended fixes (in priority order)

1. **[P1] Convert `formatRows` to computed** — 2 lines changed, no behavior change
2. **[P2] Extract `DashboardKpiGrid.vue`** — moves ~170 lines of template + 6 computed properties
3. **[P3] Extract `useAsyncData` composable** — worth doing when touching a 3rd view with the same pattern

### Effort estimate
- P1 fixes: ~10 min
- P2 splits: ~45 min each
- Total for full file: ~2.5 hours
```

---

## Agent delegation

- Use **Explore** agent to grep for patterns across many files before narrowing scope
- Use **code-reviewer** agent for independent quality assessment after the analysis
- **Delegate ALL `.vue` file edits to `vue-expert`** — provide exact before/after code, not just instructions
