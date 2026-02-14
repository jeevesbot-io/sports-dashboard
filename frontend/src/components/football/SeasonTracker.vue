<template>
  <div class="season-tracker">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading season tracker...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <VChart
      v-show="!loading && !error"
      :option="chartOption"
      :style="{ height: '350px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const loading = ref(false)
const error = ref('')
const matchdays = ref<number[]>([])
const newcastlePoints = ref<number[]>([])
const totalMatchdays = 38

// Benchmark pace lines (total points / 38 matchdays)
const BENCHMARKS = computed(() => [
  { name: 'Title Pace (90pts)', points: 90, color: chartColors.value.draw },
  { name: 'Top 4 Pace (71pts)', points: 71, color: chartColors.value.win },
  { name: 'Relegation (35pts)', points: 35, color: chartColors.value.loss },
])

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getPointsProgression()
    const data = response.data
    if (data) {
      matchdays.value = data.matchdays || []
      const newcastle = (data.series || []).find((s: any) =>
        s.name === 'Newcastle United' || s.name === 'Newcastle'
      )
      if (newcastle) {
        newcastlePoints.value = (newcastle.data || []).map((d: any) => d.points ?? d)
      }
    }
  } catch (e: any) {
    error.value = 'Failed to load season tracker data'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value
  const benchmarks = BENCHMARKS.value
  const fullMatchdays = Array.from({ length: totalMatchdays }, (_, i) => i + 1)

  // Project Newcastle's final points based on current pace
  const lastMd = matchdays.value.length
  const lastPts = newcastlePoints.value[newcastlePoints.value.length - 1] || 0
  const pace = lastMd > 0 ? lastPts / lastMd : 0
  const projectedFinal = Math.round(pace * totalMatchdays)

  // Build Newcastle actual data (null for future matchdays)
  const actualData = fullMatchdays.map(md => {
    const idx = matchdays.value.indexOf(md)
    return idx >= 0 && idx < newcastlePoints.value.length ? newcastlePoints.value[idx] : null
  })

  // Build projection line (dashed from last actual point)
  const projectionData = fullMatchdays.map(md => {
    if (md < lastMd) return null
    if (md === lastMd) return lastPts
    return Math.round(lastPts + pace * (md - lastMd))
  })

  const series: any[] = [
    {
      name: `Newcastle (proj. ${projectedFinal}pts)`,
      type: 'line',
      data: actualData,
      lineStyle: { width: 3, color: colors.accent },
      itemStyle: { color: colors.accent },
      smooth: true,
      connectNulls: false
    },
    {
      name: 'Projected',
      type: 'line',
      data: projectionData,
      lineStyle: { width: 2, color: colors.accent, type: 'dashed' },
      itemStyle: { color: colors.accent },
      showSymbol: false,
      smooth: true,
      connectNulls: false
    }
  ]

  // Add benchmark pace lines
  for (const b of benchmarks) {
    const pacePerGame = b.points / totalMatchdays
    series.push({
      name: b.name,
      type: 'line',
      data: fullMatchdays.map(md => Math.round(pacePerGame * md)),
      lineStyle: { width: 1, color: b.color, type: 'dotted' },
      itemStyle: { color: b.color },
      showSymbol: false,
      smooth: false
    })
  }

  return {
    tooltip: {
      trigger: 'axis',
      ...tooltipConfig(isDark.value)
    },
    legend: {
      data: [`Newcastle (proj. ${projectedFinal}pts)`, ...benchmarks.map(b => b.name)],
      top: 0,
      textStyle: { color: colors.text, fontSize: 10 },
      type: 'scroll'
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: {
      type: 'category',
      data: fullMatchdays,
      name: 'Matchday',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'Points',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } },
      splitLine: { lineStyle: { color: colors.gridLine } }
    },
    series,
    ...CHART_ANIMATION
  }
})
</script>
