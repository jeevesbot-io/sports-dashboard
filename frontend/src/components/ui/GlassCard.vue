<script setup lang="ts">
import { computed } from 'vue'

type CardVariant = 'default' | 'elevated' | 'outlined'
type CardPadding = 'none' | 'sm' | 'md' | 'lg'

interface Props {
  variant?: CardVariant
  glow?: boolean
  padding?: CardPadding
  interactive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  glow: false,
  padding: 'md',
  interactive: false,
})

const cardClasses = computed(() => {
  const classes: string[] = []

  if (props.variant === 'elevated') {
    classes.push('glass-card-elevated')
  } else if (props.variant === 'outlined') {
    classes.push('border border-surface-300/20 rounded-2xl')
  } else {
    classes.push('glass-card')
  }

  if (props.interactive) {
    classes.push('glass-card-interactive')
  }

  if (props.glow) {
    classes.push('shadow-glass-glow')
  }

  return classes
})

const contentPadding = computed(() => {
  const paddingMap: Record<CardPadding, string> = {
    none: '',
    sm: 'px-4 py-3',
    md: 'px-6 py-5',
    lg: 'px-8 py-7',
  }
  return paddingMap[props.padding]
})
</script>

<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="glass-card-header px-6 pt-5 pb-2">
      <slot name="header" />
    </div>
    <div :class="contentPadding">
      <slot />
    </div>
    <div v-if="$slots.footer" class="glass-card-footer px-6 pb-5 pt-2 border-t border-white/5">
      <slot name="footer" />
    </div>
  </div>
</template>
