<script setup lang="ts">
import { computed } from 'vue'
import AnimatedNumber from './AnimatedNumber.vue'

interface Props {
  value: string | number
  label: string
  icon?: string
  gradient?: string
  trend?: 'up' | 'down' | null
  trendValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: undefined,
  gradient: 'var(--sd-gradient-1)',
  trend: null,
  trendValue: undefined,
})

const numericValue = computed(() => {
  return parseFloat(String(props.value)) || 0
})

const decimals = computed(() => {
  return String(props.value).includes('.') ? 1 : 0
})

const trendClasses = computed(() => {
  if (props.trend === 'up') return 'text-green-300'
  if (props.trend === 'down') return 'text-red-300'
  return ''
})
</script>

<template>
  <div class="stat-card-glass relative overflow-hidden" :style="{ background: gradient }">
    <div class="relative z-10">
      <div class="flex items-center justify-between mb-3">
        <span class="text-white/70 text-xs font-semibold uppercase tracking-wider">{{ label }}</span>
        <i v-if="icon" :class="icon" class="text-white/20 text-2xl"></i>
      </div>
      <div class="flex items-end gap-3">
        <span class="font-display text-stat-2xl font-bold text-white leading-none">
          <AnimatedNumber :value="numericValue" :decimals="decimals" />
        </span>
        <span v-if="trend" :class="trendClasses" class="text-sm font-semibold mb-1">
          <i :class="trend === 'up' ? 'pi pi-arrow-up' : 'pi pi-arrow-down'" class="text-xs mr-1"></i>
          {{ trendValue }}
        </span>
      </div>
    </div>
    <!-- Watermark icon -->
    <i v-if="icon" :class="icon" class="absolute -bottom-2 -right-2 text-white/5 text-7xl pointer-events-none"></i>
  </div>
</template>
