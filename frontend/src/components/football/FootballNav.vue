<!--
Football Section Navigation Component
-->
<template>
  <div class="football-nav bg-surface-50 border-b border-surface-200">
    <div class="container mx-auto px-4">
      <nav class="flex items-center gap-1">
        <router-link
          v-for="tab in footballTabs"
          :key="tab.name"
          :to="tab.route"
          class="nav-link px-4 py-3 text-sm font-medium rounded-t-lg transition-all duration-200"
          :class="[
            tab.active 
              ? 'bg-white text-primary border-t-2 border-x border-primary' 
              : 'text-gray-600 hover:text-gray-800 hover:bg-surface-100'
          ]"
        >
          <i :class="[tab.icon, 'mr-2']"></i>
          {{ tab.label }}
          <Tag 
            v-if="tab.badge" 
            :value="tab.badge" 
            :severity="tab.badgeSeverity || 'info'" 
            class="ml-2 text-xs"
          />
        </router-link>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Tag from 'primevue/tag'

interface FootballTab {
  name: string
  label: string
  route: string
  icon: string
  active: boolean
  badge?: string
  badgeSeverity?: string
}

const route = useRoute()

const footballTabs = computed<FootballTab[]>(() => {
  const currentPath = route.path
  
  return [
    {
      name: 'dashboard',
      label: 'Dashboard',
      route: '/football',
      icon: 'pi pi-home',
      active: currentPath === '/football'
    },
    {
      name: 'analytics',
      label: 'Advanced Analytics',
      route: '/football/analytics',
      icon: 'pi pi-chart-line',
      active: currentPath === '/football/analytics',
      badge: 'NEW',
      badgeSeverity: 'success'
    }
  ]
})
</script>

<style scoped>
.football-nav {
  @apply sticky top-0 z-10;
}

.nav-link {
  @apply border-b-2 border-transparent;
  margin-bottom: -1px; /* Overlap the border */
}

.nav-link.router-link-exact-active {
  @apply bg-white text-primary shadow-sm;
  border-top-color: var(--primary-color);
  border-left-color: var(--surface-200);
  border-right-color: var(--surface-200);
  border-bottom-color: white;
}

.nav-link:not(.router-link-exact-active):hover {
  @apply bg-surface-100;
}

/* Mobile responsiveness */
@media (max-width: 640px) {
  .nav-link {
    @apply px-3 py-2 text-xs;
  }
  
  .nav-link i {
    @apply mr-1;
  }
}
</style>