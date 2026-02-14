<template>
  <div class="scoreline-frequency-chart">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading scoreline data...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <div v-else-if="!data" class="text-center py-8 text-[var(--sd-text-muted)]">No scoreline data available</div>
    <VChart
      v-show="!loading && !error && data"
      :option="chartOption"
      :style="{ height: chartHeight, width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import type { ScorelineAnalysisResponse } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const props = defineProps<{
  teamId: number
}>()

const { isDark, chartColors } = useChartTheme()

const loading = ref(false)
const error = ref('')
const data = ref<ScorelineAnalysisResponse | null>(null)

const chartHeight = computed(() => {
  const count = data.value?.scorelines.length || 10
  return `${Math.max(300, count * 35)}px`
})

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getScorelineFrequency(props.teamId)
    data.value = response.data || null
  } catch (e: any) {
    error.value = 'Failed to load scoreline data'
  } finally {
    loading.value = false
  }
}

watch(() => props.teamId, loadData)
onMounted(loadData)

const chartOption = computed<EChartsOption>(() => {
  if (!data.value) return {}
  const colors = chartColors.value
  const scorelines = [...data.value.scorelines].reverse() // reverse for bottom-to-top

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const idx = params[0].dataIndex
        const sl = scorelines[idx]
        return `<b>${sl.scoreline}</b><br/>Total: ${sl.count}<br/>Wins: ${sl.wins} | Draws: ${sl.draws} | Losses: ${sl.losses}`
      }
    },
    legend: {
      data: ['Wins', 'Draws', 'Losses'],
      top: 5,
      textStyle: { color: colors.text }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.gridLine, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: scorelines.map(s => s.scoreline),
      axisLabel: { color: colors.axisLabel, fontSize: 12, fontWeight: 'bold' },
      axisLine: { lineStyle: { color: colors.axis } }
    },
    series: [
      {
        name: 'Wins',
        type: 'bar',
        stack: 'total',
        data: scorelines.map(s => s.wins),
        itemStyle: { color: colors.win, borderRadius: [0, 0, 0, 0] }
      },
      {
        name: 'Draws',
        type: 'bar',
        stack: 'total',
        data: scorelines.map(s => s.draws),
        itemStyle: { color: colors.draw }
      },
      {
        name: 'Losses',
        type: 'bar',
        stack: 'total',
        data: scorelines.map(s => s.losses),
        itemStyle: { color: colors.loss, borderRadius: [0, 4, 4, 0] }
      }
    ],
    ...CHART_ANIMATION
  }
})
</script>
