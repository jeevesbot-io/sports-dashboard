<template>
  <nav class="bg-surface-800 border-b border-surface-600">
    <div class="container mx-auto px-4">
      <TabMenu 
        :model="sportTabs" 
        class="sport-navigation"
      >
        <template #item="{ item, props }">
          <router-link
            v-if="!item.comingSoon"
            v-bind="props.action"
            :to="item.route"
            class="flex items-center gap-2 p-3 font-medium transition-all duration-200"
            :class="[
              item.active 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-surface-400 hover:text-surface-200'
            ]"
          >
            <i :class="item.icon"></i>
            <span>{{ item.label }}</span>
            <Tag 
              v-if="item.active && item.name === 'football'" 
              value="LIVE" 
              severity="success" 
              class="ml-2 text-xs"
            />
          </router-link>
          
          <!-- Coming Soon Item -->
          <div
            v-else
            v-bind="props.action"
            class="flex items-center gap-2 p-3 font-medium cursor-not-allowed opacity-50"
            @click="showComingSoon(item)"
          >
            <i :class="item.icon"></i>
            <span>{{ item.label }}</span>
            <Tag 
              value="SOON" 
              severity="warning" 
              class="ml-2 text-xs"
            />
          </div>
        </template>
      </TabMenu>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import type { SportTab } from '@/types'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// Sport tab configuration
const sportTabs = computed<SportTab[]>(() => {
  const currentSport = route.meta.sport as string
  
  return [
    {
      name: 'football',
      label: 'Football',
      route: '/football',
      icon: 'pi pi-circle',
      active: currentSport === 'football',
      comingSoon: false
    },
    {
      name: 'cricket',
      label: 'Cricket',
      route: '/cricket',
      icon: 'pi pi-circle',
      active: currentSport === 'cricket',
      comingSoon: true
    },
    {
      name: 'rugby',
      label: 'Rugby',
      route: '/rugby',
      icon: 'pi pi-circle',
      active: currentSport === 'rugby',
      comingSoon: true
    }
  ]
})

// Methods
const showComingSoon = (sport: SportTab) => {
  toast.add({
    severity: 'info',
    summary: `${sport.label} Coming Soon`,
    detail: `${sport.label} analytics are currently in development. Stay tuned!`,
    life: 4000
  })
}

// Watch for route changes to update active state
watch(
  () => route.path,
  () => {
    // The computed property will automatically update
  }
)
</script>

<style scoped>
.sport-navigation {
  background: transparent;
  border: none;
}

/* Override PrimeVue TabMenu styles */
:deep(.p-tabmenu) {
  background: transparent;
  border: none;
}

:deep(.p-tabmenu-nav) {
  background: transparent;
  border: none;
  padding: 0;
}

:deep(.p-tabmenuitem) {
  margin-right: 0;
}

:deep(.p-tabmenuitem-link) {
  background: transparent;
  border: none;
  padding: 0;
  transition: all 0.2s ease;
}

:deep(.p-tabmenuitem-link:hover) {
  background: transparent;
}

:deep(.p-tabmenuitem-link:focus) {
  box-shadow: none;
}

/* Custom active state */
.router-link-exact-active {
  color: var(--primary-color) !important;
  border-bottom-color: var(--primary-color) !important;
}

/* Newcastle branding for football tab when active */
.router-link-exact-active[href="/football"] {
  color: #ffffff !important;
  border-bottom-color: #ffffff !important;
  background: linear-gradient(45deg, #000000, #333333);
  border-radius: 4px 4px 0 0;
}

/* Responsive design */
@media (max-width: 640px) {
  :deep(.p-tabmenu-nav) {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .flex.items-center.gap-2 {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
  }
}

/* Coming soon hover effect */
.cursor-not-allowed:hover {
  background: rgba(var(--surface-400), 0.1);
  border-radius: 4px;
  transition: background 0.2s ease;
}
</style>