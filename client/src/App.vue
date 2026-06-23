<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <div class="app-main">
      <Topbar :collapsed="sidebarCollapsed">
        <LanguageSwitcher />
        <ProfileMenu @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />
      </Topbar>
      <FilterBar />
      <main class="app-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    Sidebar,
    Topbar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar state: user preference (persisted) + narrow-viewport override
    const STORAGE_KEY = 'sidebar-collapsed'
    const BREAKPOINT = 1280

    const userCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')
    const isNarrow = ref(window.innerWidth <= BREAKPOINT)

    // Effective collapsed = narrow screen OR user manually collapsed
    const sidebarCollapsed = computed(() => isNarrow.value || userCollapsed.value)

    // Persist only the user's manual preference
    watch(userCollapsed, v => localStorage.setItem(STORAGE_KEY, String(v)))

    // Toggle handler: only change user preference (not the narrow override)
    const toggleSidebar = () => {
      if (!isNarrow.value) {
        userCollapsed.value = !userCollapsed.value
      }
    }

    // Resize listener — update isNarrow, restore user pref when widening
    const onResize = () => {
      isNarrow.value = window.innerWidth <= BREAKPOINT
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      window.addEventListener('resize', onResize)
    })

    onUnmounted(() => window.removeEventListener('resize', onResize))

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      sidebarCollapsed,
      toggleSidebar
    }
  }
}
</script>

<style>
:root {
  /* Map app vars to Dallask tokens */
  --sidebar-width: var(--dk-sidebar-width);
  --sidebar-collapsed-width: var(--dk-sidebar-collapsed);
  --sidebar-bg: var(--dk-surface-2);
  --sidebar-border: var(--dk-border);
  --sidebar-item-hover: var(--dk-surface-3);
  --sidebar-item-active-bg: var(--dk-primary);
  --sidebar-item-active-text: var(--dk-text-on-accent);
  --sidebar-text: var(--dk-text-secondary);
  --sidebar-text-hover: var(--dk-text-heading);
  --sidebar-icon-size: 20px;
  --topbar-height: var(--dk-topbar-height);
  --topbar-bg: var(--dk-surface-2);
  --topbar-border: var(--dk-border);
  --content-bg: var(--dk-bg);
  --content-padding: 1.75rem 2rem;
  --surface-1: var(--dk-surface-1);
  --surface-2: var(--dk-surface-2);
  --border-color: var(--dk-border);
  --text-primary: var(--dk-text-heading);
  --text-secondary: var(--dk-text-secondary);
  --text-muted: var(--dk-text-muted);
  --accent: var(--dk-primary);
  --accent-hover: var(--dk-primary-hover);
  --status-green: var(--dk-success);
  --status-blue: var(--dk-info);
  --status-amber: var(--dk-warning);
  --status-red: var(--dk-danger);
  --transition-sidebar: width 0.2s ease;
  --transition-fast: 0.15s ease;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--dk-font-body);
  background: var(--content-bg);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

/* Shell grid */
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

/* Page header */
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-family: var(--dk-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--dk-text-heading);
  letter-spacing: -0.025em;
  margin-bottom: 0.25rem;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

/* Stat card */
.stat-card {
  background: var(--surface-1);
  padding: 1.25rem 1.5rem;
  border-radius: 0;
  border: 1px solid var(--border-color);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--dk-border-strong);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--dk-warning); }
.stat-card.success .stat-value { color: var(--dk-success); }
.stat-card.danger  .stat-value { color: var(--dk-danger); }
.stat-card.info    .stat-value { color: var(--dk-info); }

/* Card */
.card {
  background: var(--surface-1);
  border-radius: 0;
  padding: 1.25rem 1.5rem;
  border: 1px solid var(--border-color);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

/* Table */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--dk-surface-1);
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--dk-border-subtle);
  color: var(--text-primary);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--surface-2);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 0;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.badge.success    { background: var(--dk-success-subtle); color: var(--dk-success-text); }
.badge.warning    { background: var(--dk-warning-subtle); color: var(--dk-warning-text); }
.badge.danger     { background: var(--dk-danger-subtle);  color: var(--dk-danger-text); }
.badge.info       { background: var(--dk-info-subtle);    color: var(--dk-info-text); }
.badge.increasing { background: var(--dk-success-subtle); color: var(--dk-success-text); }
.badge.decreasing { background: var(--dk-danger-subtle);  color: var(--dk-danger-text); }
.badge.stable     { background: var(--dk-primary-subtle); color: var(--dk-primary-text); }
.badge.high       { background: var(--dk-danger-subtle);  color: var(--dk-danger-text); }
.badge.medium     { background: var(--dk-warning-subtle); color: var(--dk-warning-text); }
.badge.low        { background: var(--dk-info-subtle);    color: var(--dk-info-text); }

/* Loading / error */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.error {
  background: var(--dk-danger-subtle);
  border: 1px solid var(--dk-danger);
  color: var(--dk-danger-text);
  padding: 1rem;
  border-radius: 0;
  margin: 1rem 0;
  font-size: 0.875rem;
}
</style>
