<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  value: number
  duration?: number
  decimals?: number
  prefix?: string
  suffix?: string
}

const props = withDefaults(defineProps<Props>(), {
  duration: 800,
  decimals: 0,
  prefix: '',
  suffix: '',
})

const displayValue = ref(0)
let animationFrameId: number | null = null

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

function animateTo(target: number) {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }

  const startValue = displayValue.value
  const startTime = performance.now()
  const diff = target - startValue

  function step(currentTime: number) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / props.duration, 1)
    const easedProgress = easeOutCubic(progress)

    displayValue.value = startValue + diff * easedProgress

    if (progress < 1) {
      animationFrameId = requestAnimationFrame(step)
    } else {
      displayValue.value = target
      animationFrameId = null
    }
  }

  animationFrameId = requestAnimationFrame(step)
}

const formattedValue = computed(() => {
  return displayValue.value.toFixed(props.decimals)
})

onMounted(() => {
  animateTo(props.value)
})

watch(
  () => props.value,
  (newVal) => {
    animateTo(newVal)
  }
)

onBeforeUnmount(() => {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }
})
</script>

<template>
  <span class="tabular-nums">{{ prefix }}{{ formattedValue }}{{ suffix }}</span>
</template>
