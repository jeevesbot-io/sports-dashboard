<template>
  <div id="app" class="min-h-screen bg-[var(--sd-surface-0)] text-[var(--sd-text-primary)]">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main Area -->
    <div class="main-area" :style="{ marginLeft: sidebarWidth }">
      <!-- Top Bar -->
      <TopBar>
        <template #actions>
          <button v-if="globalError" @click="retryLastAction"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors">
            <i class="pi pi-exclamation-triangle text-xs"></i>
            Error — Retry
          </button>
        </template>
      </TopBar>

      <!-- Main Content -->
      <main class="px-6 py-6 max-w-[1400px] mx-auto">
        <Toast />
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import AppSidebar from '@/components/common/AppSidebar.vue'
import TopBar from '@/components/common/TopBar.vue'
import { useFootballStore } from '@/stores/football'
import { useSidebar } from '@/composables/useSidebar'
import apiClient from '@/api'

const route = useRoute()
const toast = useToast()
const footballStore = useFootballStore()
const { sidebarWidth } = useSidebar()

const globalError = computed(() => footballStore.error)

const retryLastAction = () => {
  footballStore.clearError()
  if (route.meta.sport === 'football') {
    footballStore.initializeDashboard()
  }
}

const checkApiHealth = async () => {
  try {
    await apiClient.health()
  } catch {
    toast.add({
      severity: 'warn',
      summary: 'Connection Warning',
      detail: 'Unable to connect to the backend API. Some features may not work.',
      life: 5000
    })
  }
}

onMounted(async () => {
  await checkApiHealth()
})

watch(() => route.path, () => {
  footballStore.clearError()
})
</script>

<style>
/* Minimal global styles — most now in design system CSS files */
#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.main-area {
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

@media (max-width: 1023px) {
  .main-area {
    margin-left: 0 !important;
  }
}
</style>
