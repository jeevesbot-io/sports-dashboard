<script setup lang="ts">
import { computed } from 'vue'

type BadgeVariant = 'win' | 'draw' | 'loss' | 'live' | 'soon' | 'new' | 'mock' | 'default'
type BadgeSize = 'sm' | 'md'

interface Props {
  label: string
  variant?: BadgeVariant
  size?: BadgeSize
  pulse?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'sm',
  pulse: false,
})

const variantClasses: Record<BadgeVariant, string> = {
  win: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
  draw: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  loss: 'bg-red-500/15 text-red-400 border border-red-500/25',
  live: 'bg-red-500/15 text-red-400 border border-red-500/25',
  soon: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  new: 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25',
  mock: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  default: 'bg-surface-500/15 text-[var(--sd-text-secondary)] border border-surface-500/25',
}

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'px-2.5 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
}

const badgeClasses = computed(() => {
  return [
    'inline-flex items-center rounded-full font-semibold',
    sizeClasses[props.size],
    variantClasses[props.variant],
  ]
})
</script>

<template>
  <span :class="badgeClasses">
    <span v-if="pulse" class="animate-pulse-subtle inline-block w-1.5 h-1.5 rounded-full bg-current mr-1.5"></span>
    {{ label }}
  </span>
</template>
