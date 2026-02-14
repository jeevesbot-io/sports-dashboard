<script setup lang="ts">
type SkeletonVariant = 'card' | 'table' | 'chart' | 'stat-row'

interface Props {
  variant?: SkeletonVariant
  rows?: number
  cols?: number
}

withDefaults(defineProps<Props>(), {
  variant: 'card',
  rows: 5,
  cols: 4,
})
</script>

<template>
  <!-- Card variant -->
  <div v-if="variant === 'card'" class="skeleton-shimmer w-full rounded-2xl" style="height: 200px"></div>

  <!-- Stat row variant -->
  <div
    v-else-if="variant === 'stat-row'"
    class="grid gap-4"
    :style="{ gridTemplateColumns: `repeat(${cols}, 1fr)` }"
  >
    <div v-for="i in cols" :key="i" class="skeleton-shimmer h-24 rounded-xl"></div>
  </div>

  <!-- Table variant -->
  <div v-else-if="variant === 'table'">
    <div class="skeleton-shimmer h-10 w-full rounded-lg"></div>
    <div v-for="i in rows" :key="i" class="skeleton-shimmer h-12 w-full rounded-lg mt-2"></div>
  </div>

  <!-- Chart variant -->
  <div v-else-if="variant === 'chart'" class="skeleton-shimmer w-full rounded-xl" style="height: 300px"></div>
</template>
