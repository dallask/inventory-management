<template>
  <header class="topbar">
    <div class="topbar-left">
      <h2 class="page-title">{{ currentTitle }}</h2>
    </div>
    <div class="topbar-right">
      <slot />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const TITLES = {
  '/': 'Dashboard',
  '/inventory': 'Inventory',
  '/orders': 'Orders',
  '/spending': 'Spending',
  '/demand': 'Demand Forecast',
  '/reports': 'Reports',
  '/restocking': 'Restocking'
}

const route = useRoute()
const currentTitle = computed(() => TITLES[route.path] ?? 'FactoryIQ')
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-height);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--topbar-border);
  padding: 0 1.5rem;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 110;
  gap: 1rem;
}

.topbar-left {
  display: flex;
  align-items: center;
  min-width: 0;
}

.page-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}
</style>
