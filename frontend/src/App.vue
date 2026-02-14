<template>
  <div id="app" class="min-h-screen bg-surface-900 text-surface-0">
    <!-- Navigation Header -->
    <AppHeader />
    
    <!-- Sport Navigation Tabs -->
    <SportNav v-if="showSportNav" />
    
    <!-- Main Content -->
    <main class="container mx-auto px-4 py-6">
      <Toast />
      
      <!-- Error Display -->
      <Card v-if="globalError" class="mb-6 border-red-500 bg-red-50 dark:bg-red-900/20">
        <template #title>
          <div class="flex items-center gap-2 text-red-600 dark:text-red-400">
            <i class="pi pi-exclamation-triangle"></i>
            Error
          </div>
        </template>
        <template #content>
          <p class="text-red-700 dark:text-red-300">{{ globalError }}</p>
          <Button 
            label="Retry" 
            severity="danger" 
            outlined 
            size="small" 
            @click="retryLastAction" 
            class="mt-3"
          />
        </template>
      </Card>
      
      <!-- Router View -->
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <!-- Footer -->
    <footer class="mt-auto py-6 text-center text-surface-400">
      <p>&copy; 2025 Sports Dashboard. Built with Vue 3, FastAPI & PostgreSQL.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import AppHeader from '@/components/common/AppHeader.vue'
import SportNav from '@/components/common/SportNav.vue'
import { useFootballStore } from '@/stores/football'
import apiClient from '@/api'

const route = useRoute()
const toast = useToast()
const footballStore = useFootballStore()

// Computed properties
const showSportNav = computed(() => {
  return route.path !== '/'
})

const globalError = computed(() => {
  return footballStore.error
})

// Methods
const retryLastAction = () => {
  footballStore.clearError()
  // Could implement more sophisticated retry logic here
  if (route.meta.sport === 'football') {
    footballStore.initializeDashboard()
  }
}

const checkApiHealth = async () => {
  try {
    await apiClient.health()
  } catch (error) {
    toast.add({
      severity: 'warn',
      summary: 'Connection Warning',
      detail: 'Unable to connect to the backend API. Some features may not work.',
      life: 5000
    })
  }
}

// Lifecycle
onMounted(async () => {
  await checkApiHealth()
})

// Watch for route changes to clear errors
watch(() => route.path, () => {
  footballStore.clearError()
})
</script>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Page transition animations */
.page-enter-active,
.page-leave-active {
  transition: all 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
}

/* Newcastle branding colors */
.newcastle-primary {
  color: #000000;
}

.newcastle-secondary {
  color: #ffffff;
}

.bg-newcastle-primary {
  background-color: #000000;
}

.bg-newcastle-secondary {
  background-color: #ffffff;
}

/* Custom scrollbar for dark theme */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--surface-100);
}

::-webkit-scrollbar-thumb {
  background: var(--surface-400);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--surface-500);
}

/* Responsive design helpers */
.container {
  max-width: 1200px;
}

@media (max-width: 768px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}

/* PrimeVue DataTable customizations for dark theme */
.p-datatable .p-datatable-tbody > tr:nth-child(odd) {
  background-color: var(--surface-50);
}

.p-datatable .p-datatable-tbody > tr:nth-child(even) {
  background-color: var(--surface-0);
}

/* Loading state improvements */
.p-skeleton {
  background: linear-gradient(90deg, var(--surface-200) 25%, var(--surface-100) 50%, var(--surface-200) 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>