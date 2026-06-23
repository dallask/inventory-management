<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
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
import { ref, onMounted, computed, watch } from 'vue'
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

    // Sidebar collapse state persisted to localStorage
    const STORAGE_KEY = 'sidebar-collapsed'
    const sidebarCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')
    watch(sidebarCollapsed, v => localStorage.setItem(STORAGE_KEY, String(v)))

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

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      sidebarCollapsed
    }
  }
}
</script>

<style>
:root {
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
  --topbar-height: 56px;
  --topbar-bg: #0f172a;
  --topbar-border: #1e293b;
  --content-bg: #0f172a;
  --content-padding: 1.75rem 2rem;
  --surface-1: #1e293b;
  --surface-2: #253347;
  --border-color: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #475569;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --status-green: #22c55e;
  --status-blue: #3b82f6;
  --status-amber: #f59e0b;
  --status-red: #f43f5e;
  --transition-sidebar: width 0.2s ease;
  --transition-fast: 0.15s ease;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
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
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.stat-card:hover {
  border-color: #475569;
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

.stat-card.warning .stat-value { color: var(--status-amber); }
.stat-card.success .stat-value { color: var(--status-green); }
.stat-card.danger  .stat-value { color: var(--status-red); }
.stat-card.info    .stat-value { color: var(--status-blue); }

/* Card */
.card {
  background: var(--surface-1);
  border-radius: 10px;
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
  background: #0f172a;
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
  border-top: 1px solid #1e293b;
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
  border-radius: 5px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.badge.success    { background: #14532d; color: #86efac; }
.badge.warning    { background: #78350f; color: #fde68a; }
.badge.danger     { background: #7f1d1d; color: #fca5a5; }
.badge.info       { background: #1e3a5f; color: #93c5fd; }
.badge.increasing { background: #14532d; color: #86efac; }
.badge.decreasing { background: #7f1d1d; color: #fca5a5; }
.badge.stable     { background: #1e1b4b; color: #c4b5fd; }
.badge.high       { background: #7f1d1d; color: #fca5a5; }
.badge.medium     { background: #78350f; color: #fde68a; }
.badge.low        { background: #1e3a5f; color: #93c5fd; }

/* Loading / error */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.error {
  background: #450a0a;
  border: 1px solid #7f1d1d;
  color: #fca5a5;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.875rem;
}
</style>
