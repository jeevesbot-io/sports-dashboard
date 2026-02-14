<template>
  <header class="sticky top-0 z-20 h-14 flex items-center justify-between px-6 border-b border-[var(--sd-glass-border)] bg-[var(--sd-surface-0)]/80 backdrop-blur-xl">
    <!-- Left: hamburger (mobile) + breadcrumb -->
    <div class="flex items-center gap-3">
      <button v-if="!isDesktop" @click="toggleMobile" class="p-2 rounded-lg hover:bg-[var(--sd-surface-200)] transition-colors">
        <i class="pi pi-bars text-[var(--sd-text-secondary)]"></i>
      </button>
      <nav class="flex items-center gap-1.5 text-sm">
        <template v-for="(crumb, i) in breadcrumbs" :key="i">
          <span v-if="i > 0" class="text-[var(--sd-text-muted)]">/</span>
          <router-link v-if="crumb.to" :to="crumb.to" class="text-[var(--sd-text-muted)] hover:text-[var(--sd-text-primary)] transition-colors no-underline">
            {{ crumb.label }}
          </router-link>
          <span v-else class="text-[var(--sd-text-primary)] font-medium">{{ crumb.label }}</span>
        </template>
      </nav>
    </div>

    <!-- Right: actions -->
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'

const route = useRoute()
const { isDesktop, toggleMobile } = useSidebar()

const breadcrumbs = computed(() => {
  const crumbs: { label: string; to?: string }[] = []
  const path = route.path

  if (path === '/') {
    crumbs.push({ label: 'Home' })
  } else if (path.startsWith('/football')) {
    crumbs.push({ label: 'Football', to: '/football' })
    if (path === '/football') {
      crumbs.push({ label: 'Dashboard' })
    } else if (path === '/football/analytics') {
      crumbs.push({ label: 'Analytics' })
    } else if (path.includes('/teams/')) {
      crumbs.push({ label: 'Team Detail' })
    }
  } else if (path.startsWith('/cricket')) {
    crumbs.push({ label: 'Cricket' })
  } else if (path.startsWith('/rugby')) {
    crumbs.push({ label: 'Rugby' })
  }

  return crumbs
})
</script>
