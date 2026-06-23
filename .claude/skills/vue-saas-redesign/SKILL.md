---
name: vue-saas-redesign
description: >
  Redesigns a Vue 3 application's UI into a modern SaaS-style interface:
  vertical collapsible sidebar navigation replacing a top nav bar, a sticky topbar,
  consistent design tokens, and a polished professional look.
  Invoke when the user asks to "redesign the UI", "add a sidebar", "switch to
  vertical nav", or "make this look like a SaaS app".
---

# Vue 3 SaaS Redesign Skill

## When to invoke
- User asks to redesign/modernize the UI
- User wants a sidebar instead of a top nav bar
- User wants a "SaaS-style", "dashboard-style", or "professional" look
- User wants consistent spacing, design tokens, or a polished layout

## Agent delegation rule
**ANY time you create or significantly modify a `.vue` file you MUST delegate to the `vue-expert` agent.** Use this skill to plan the phases and generate the exact code to hand off.

---

## Phase overview

| # | Phase | What changes |
|---|-------|-------------|
| 1 | Design tokens | CSS custom properties in `App.vue` `<style>` |
| 2 | App shell | `App.vue` layout: sidebar + topbar + `<router-view>` |
| 3 | Sidebar component | `Sidebar.vue` — nav links, icons, collapse |
| 4 | Topbar component | `Topbar.vue` — page title, breadcrumb, user controls |
| 5 | Remove old nav | Delete `.top-nav` styles and markup from `App.vue` |
| 6 | View adjustments | Remove per-view padding that assumed top-nav; fix widths |
| 7 | Polish & verify | Transitions, active states, responsive, localStorage persistence |

Run phases sequentially. Each produces a self-contained deliverable.

---

## Phase 1 — Design tokens

Add to the `:root` block in `App.vue` (or a dedicated `src/styles/tokens.css`):

```css
:root {
  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 64px;
  --sidebar-bg: #0f172a;
  --sidebar-border: #1e293b;
  --sidebar-item-hover: #1e293b;
  --sidebar-item-active-bg: #1d4ed8;
  --sidebar-item-active-text: #ffffff;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #f1f5f9;
  --sidebar-icon-size: 20px;

  /* Topbar */
  --topbar-height: 56px;
  --topbar-bg: #0f172a;
  --topbar-border: #1e293b;

  /* Layout */
  --content-bg: #0f172a;
  --content-padding: 1.75rem 2rem;

  /* Surface / cards */
  --surface-1: #1e293b;
  --surface-2: #253347;
  --border-color: #334155;

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #475569;

  /* Accent */
  --accent: #3b82f6;
  --accent-hover: #2563eb;

  /* Status */
  --status-green: #22c55e;
  --status-blue: #3b82f6;
  --status-amber: #f59e0b;
  --status-red: #f43f5e;

  /* Transitions */
  --transition-sidebar: width 0.2s ease, opacity 0.15s ease;
  --transition-fast: 0.15s ease;
}
```

---

## Phase 2 — App shell (`App.vue`)

Replace the existing template with this two-column CSS-grid shell. The sidebar occupies the left column; the right column stacks the topbar above the router-view.

```html
<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <Sidebar
      :collapsed="sidebarCollapsed"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
    />
    <div class="app-main">
      <Topbar :collapsed="sidebarCollapsed" />
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'

const STORAGE_KEY = 'sidebar-collapsed'
const sidebarCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')
watch(sidebarCollapsed, v => localStorage.setItem(STORAGE_KEY, v))
</script>

<style>
/* --- Reset & base --- */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--content-bg);
  color: var(--text-primary);
  line-height: 1.5;
}

/* --- Shell grid --- */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--transition-sidebar);
}
.app-shell.sidebar-collapsed {
  grid-template-columns: var(--sidebar-collapsed-width) 1fr;
}

.app-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow: hidden;
}

.app-content {
  flex: 1;
  padding: var(--content-padding);
  overflow-y: auto;
}
</style>
```

---

## Phase 3 — Sidebar component (`src/components/Sidebar.vue`)

Key behaviours:
- Emits `toggle` to parent (parent owns collapsed state + localStorage)
- Router links use `router-link` with `active-class="active"`
- Labels hidden with `v-show` (not `v-if`) so width transition is smooth
- Icons are inline SVG paths — no icon library needed

```html
<template>
  <aside class="sidebar" :class="{ collapsed }">

    <!-- Logo / brand -->
    <div class="sidebar-brand">
      <span class="brand-icon">▣</span>
      <span v-show="!collapsed" class="brand-name">Inventory</span>
    </div>

    <!-- Nav links -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="active"
      >
        <span class="nav-icon" v-html="item.icon" />
        <span v-show="!collapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Collapse toggle at the bottom -->
    <button class="sidebar-toggle" @click="$emit('toggle')" :title="collapsed ? 'Expand' : 'Collapse'">
      <span class="nav-icon" v-html="collapsed ? iconExpand : iconCollapse" />
    </button>

  </aside>
</template>

<script setup>
defineProps({ collapsed: Boolean })
defineEmits(['toggle'])

/* Inline SVG icons — replace paths to match your design system */
const navItems = [
  {
    to: '/',
    label: 'Dashboard',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>`,
  },
  {
    to: '/inventory',
    label: 'Inventory',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    </svg>`,
  },
  {
    to: '/orders',
    label: 'Orders',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>`,
  },
  {
    to: '/spending',
    label: 'Spending',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
    </svg>`,
  },
  {
    to: '/demand',
    label: 'Demand',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>`,
  },
  {
    to: '/reports',
    label: 'Reports',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
    </svg>`,
  },
]

const iconCollapse = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>`
const iconExpand   = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>`
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  overflow: hidden;
  transition: var(--transition-sidebar);
}
.sidebar.collapsed { width: var(--sidebar-collapsed-width); }

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.25rem;
  height: var(--topbar-height);
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}
.brand-icon { font-size: 1.25rem; color: var(--accent); flex-shrink: 0; }
.brand-name { font-weight: 700; font-size: 0.95rem; color: var(--text-primary); white-space: nowrap; }

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-item:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-hover);
}
.nav-item.active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-item-active-text);
}

.nav-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--sidebar-icon-size);
  height: var(--sidebar-icon-size);
}
.nav-label { overflow: hidden; }

/* Collapse toggle */
.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.85rem 0.75rem;
  background: none;
  border: none;
  border-top: 1px solid var(--sidebar-border);
  color: var(--sidebar-text);
  cursor: pointer;
  width: 100%;
  font-size: 0.8rem;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.sidebar-toggle:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-hover); }
</style>
```

---

## Phase 4 — Topbar component (`src/components/Topbar.vue`)

The topbar shows the current route's title on the left and user controls (language switcher, profile menu) on the right. It replaces the old top nav bar's user-facing controls.

```html
<template>
  <header class="topbar">
    <div class="topbar-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>
    <div class="topbar-right">
      <!-- Drop your existing LanguageSwitcher and ProfileMenu here -->
      <slot />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({ collapsed: Boolean })

const route = useRoute()

/* Map route names/paths to display titles */
const TITLES = {
  '/': 'Dashboard',
  '/inventory': 'Inventory',
  '/orders': 'Orders',
  '/spending': 'Spending',
  '/demand': 'Demand Forecast',
  '/reports': 'Reports',
  '/backlog': 'Backlog',
}
const pageTitle = computed(() => TITLES[route.path] ?? route.name ?? 'Dashboard')
</script>

<style scoped>
.topbar {
  height: var(--topbar-height);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--topbar-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.75rem;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}
.page-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
```

---

## Phase 5 — Remove the old top nav

In `App.vue`, delete:
- The `<nav class="top-nav">` (or equivalent) element and all its children
- All `.top-nav`, `.nav-links`, `.nav-brand`, `.hamburger` CSS rules
- Any `showMobileMenu` / `mobileMenuOpen` refs and event handlers tied to top-nav

Move any user controls (LanguageSwitcher, ProfileMenu, TasksModal trigger) into the `<Topbar>` slot:

```html
<!-- In App.vue, update Topbar usage: -->
<Topbar :collapsed="sidebarCollapsed">
  <LanguageSwitcher />
  <ProfileMenu @open-tasks="showTasksModal = true" @open-profile="showProfileModal = true" />
</Topbar>
```

---

## Phase 6 — View adjustments checklist

After removing the top nav, audit each view file:

- [ ] **Remove top padding / margin** that was compensating for the fixed top nav (often `padding-top: 60px` or `margin-top: var(--nav-height)`)
- [ ] **Remove max-width constraints** that assumed a full-width layout — sidebar already constrains the content area width
- [ ] **Replace `.container` wrappers** that added horizontal padding (the `--content-padding` on `.app-content` now handles this)
- [ ] **Check table/grid widths** — `width: 100%` tables may now be too wide; verify they scroll horizontally on narrow viewports
- [ ] **Filter bar** — if `FilterBar.vue` was inside the top nav, move it below the `<Topbar>` in `App.vue` or at the top of each view that needs it
- [ ] **z-index audit** — any `position: fixed` modals/overlays must be `z-index` above the sidebar (`z-index: 100+`)

---

## Phase 7 — Polish checklist

- [ ] Sidebar collapse animation is smooth (CSS `transition` on `width`, not `display`)
- [ ] Active nav item highlights correctly for all 6+ routes
- [ ] Collapsed sidebar shows only icons (tooltips via `title` attr on `.nav-item`)
- [ ] Page title in Topbar updates on every route change
- [ ] localStorage persists collapse state across page reloads
- [ ] No horizontal scrollbar on the page body in expanded or collapsed state
- [ ] Modals overlay both sidebar and content (`position: fixed; z-index: 200`)
- [ ] Run the app: `cd client && npm run dev` — walk every route and verify

---

## Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Content area overflows horizontally | Old `width: 100vw` on a view | Change to `width: 100%` |
| Sidebar not sticky on tall pages | `height: 100%` instead of `height: 100vh` + `position: sticky; top: 0` | Fix sidebar CSS |
| Active class not applied | Wrong `active-class` prop or route path mismatch | Use exact routes or `exact-active-class` |
| Collapse flickers on reload | Reading `localStorage` after render | Initialize `sidebarCollapsed` ref directly from `localStorage.getItem()` |
| Modal appears behind sidebar | Modal `z-index` too low | Ensure modal wrapper is `position: fixed; z-index: 200+` |
| Label visible in collapsed state | Using `v-if` instead of `v-show` on labels | Use `v-show` so CSS transition runs |

---

## Verification steps

After all phases, run through this checklist in the browser:

1. App loads with sidebar visible — correct default collapse state from localStorage
2. Click collapse button — sidebar shrinks to icon-only mode, content area expands
3. Navigate to every route — active icon highlights, page title updates
4. Reload on any route — sidebar collapse state preserved
5. Open a modal — modal overlays both sidebar and content
6. Resize window to ~1024px — no horizontal overflow
7. FilterBar (if present) functions identically to before
