<script setup lang="ts">
import GlassCard from './GlassCard.vue'

interface Props {
  title: string
  subtitle?: string
  loading?: boolean
  error?: string | null
  height?: string
}

withDefaults(defineProps<Props>(), {
  subtitle: undefined,
  loading: false,
  error: null,
  height: '350px',
})

defineEmits<{
  retry: []
}>()
</script>

<template>
  <GlassCard padding="none">
    <template #header>
      <div class="flex items-center justify-between px-6 pt-5 pb-2">
        <div>
          <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">{{ title }}</h3>
          <p v-if="subtitle" class="text-sm text-[var(--sd-text-muted)] mt-0.5">{{ subtitle }}</p>
        </div>
        <div v-if="$slots.actions" class="flex gap-2">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <div class="px-6 pb-5" :style="{ minHeight: height }">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-full" :style="{ minHeight: height }">
        <div class="skeleton-shimmer w-full h-full rounded-lg"></div>
      </div>
      <!-- Error -->
      <div v-else-if="error" class="flex flex-col items-center justify-center gap-3" :style="{ minHeight: height }">
        <i class="pi pi-exclamation-circle text-3xl text-[var(--sd-loss)]"></i>
        <p class="text-sm text-[var(--sd-text-muted)]">{{ error }}</p>
        <button @click="$emit('retry')" class="pill-nav-item pill-nav-item-active text-xs">Retry</button>
      </div>
      <!-- Chart content -->
      <div v-else>
        <slot />
      </div>
    </div>
  </GlassCard>
</template>
