<template>
  <aside :class="sidebarClasses" class="sidebar">
    <!-- Logo -->
    <div class="flex items-center gap-3 px-5 py-5">
      <router-link to="/" class="flex items-center gap-3 no-underline">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
             style="background: var(--sd-accent-gradient)">
          <i class="pi pi-chart-line text-white text-lg"></i>
        </div>
        <span v-if="!isCollapsed" class="font-display text-lg font-bold text-[var(--sd-text-primary)]">
          Sports<span class="gradient-text">Dash</span>
        </span>
      </router-link>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 mt-2 overflow-y-auto">
      <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--sd-text-muted)] px-3 mb-2">
        Sports
      </div>

      <!-- Football Group -->
      <div class="mb-1">
        <button @click="footballExpanded = !footballExpanded"
                :class="['nav-item w-full', isFootballActive ? 'nav-item-active' : '']">
          <i class="pi pi-futbol text-base"></i>
          <span v-if="!isCollapsed" class="flex-1 text-left">Football</span>
          <i v-if="!isCollapsed" :class="['pi text-xs transition-transform', footballExpanded ? 'pi-chevron-down' : 'pi-chevron-right']"></i>
        </button>
        <div v-if="footballExpanded && !isCollapsed" class="ml-5 mt-1 space-y-0.5">
          <router-link to="/football" class="nav-sub-item" active-class="nav-sub-item-active">
            <i class="pi pi-th-large text-xs"></i>
            Dashboard
          </router-link>
          <router-link to="/football/analytics" class="nav-sub-item" active-class="nav-sub-item-active">
            <i class="pi pi-chart-bar text-xs"></i>
            Analytics
          </router-link>
        </div>
      </div>

      <!-- Cricket -->
      <div class="nav-item nav-item-disabled mb-1">
        <i class="pi pi-circle text-base"></i>
        <span v-if="!isCollapsed" class="flex-1">Cricket</span>
        <span v-if="!isCollapsed" class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/25">SOON</span>
      </div>

      <!-- Rugby -->
      <div class="nav-item nav-item-disabled">
        <i class="pi pi-circle text-base"></i>
        <span v-if="!isCollapsed" class="flex-1">Rugby</span>
        <span v-if="!isCollapsed" class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/25">SOON</span>
      </div>
    </nav>

    <!-- Bottom Area -->
    <div class="px-3 pb-5 mt-auto space-y-2">
      <!-- Theme Toggle -->
      <button @click="toggleDark()" class="nav-item w-full">
        <i :class="themeIcon" class="text-base"></i>
        <span v-if="!isCollapsed">{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
      </button>

      <!-- Connection Status -->
      <div v-if="!isCollapsed" class="flex items-center gap-2 px-3 py-2">
        <div :class="['status-dot', isOnline ? 'status-dot-connected' : 'status-dot-disconnected']"></div>
        <span class="text-xs text-[var(--sd-text-muted)]">{{ isOnline ? 'Connected' : 'Offline' }}</span>
      </div>
    </div>
  </aside>

  <!-- Mobile overlay -->
  <div v-if="showOverlay" class="fixed inset-0 bg-black/50 z-30 lg:hidden" @click="closeMobile"></div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { useSidebar } from '@/composables/useSidebar'
import apiClient from '@/api'

const route = useRoute()
const { isDark, toggleDark, themeIcon } = useTheme()
const { isCollapsed, isMobileOpen, isDesktop, showOverlay, closeMobile } = useSidebar()

const footballExpanded = ref(true)
const isOnline = ref(true)

const isFootballActive = computed(() => {
  return route.path.startsWith('/football')
})

const sidebarClasses = computed(() => [
  'fixed top-0 left-0 h-full z-40 flex flex-col',
  'border-r border-[var(--sd-glass-border)]',
  'bg-[var(--sd-glass-bg)] backdrop-blur-[20px]',
  'transition-all duration-300',
  isDesktop.value
    ? (isCollapsed.value ? 'w-16' : 'w-[260px]')
    : (isMobileOpen.value ? 'w-[260px] translate-x-0' : 'w-[260px] -translate-x-full'),
])

const checkConnection = async () => {
  try {
    await apiClient.health()
    isOnline.value = true
  } catch {
    isOnline.value = false
  }
}

onMounted(() => {
  checkConnection()
  setInterval(checkConnection, 30000)
})
</script>

<style scoped>
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--sd-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
  background: transparent;
  text-decoration: none;
}

.nav-item:hover {
  color: var(--sd-text-primary);
  background: var(--sd-surface-200);
}

.nav-item-active {
  color: var(--sd-accent-cyan);
  background: rgba(6, 182, 212, 0.1);
  position: relative;
}

.nav-item-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  background: var(--sd-accent-gradient);
  border-radius: 0 2px 2px 0;
}

.nav-item-disabled {
  opacity: 0.5;
  cursor: default;
  pointer-events: none;
}

.nav-sub-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 8px;
  font-size: 0.8125rem;
  color: var(--sd-text-muted);
  text-decoration: none;
  transition: all 0.15s ease;
}

.nav-sub-item:hover {
  color: var(--sd-text-primary);
  background: var(--sd-surface-200);
}

.nav-sub-item-active {
  color: var(--sd-accent-cyan) !important;
  background: rgba(6, 182, 212, 0.08);
}
</style>
