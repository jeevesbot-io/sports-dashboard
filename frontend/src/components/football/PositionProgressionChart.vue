<template>
  <div class="position-progression-chart">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading position data...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <VChart
      v-show="!loading && !error"
      :option="chartOption"
      :style="{ height: '500px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import type { PositionProgressionResponse } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION, SERIES_COLORS } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const loading = ref(false)
const error = ref('')
const data = ref<PositionProgressionResponse | null>(null)

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getPositionProgression()
    data.value = response.data || null
  } catch (e: any) {
    error.value = 'Failed to load position progression data'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const chartOption = computed<EChartsOption>(() => {
  if (!data.value) return {}
  const colors = chartColors.value
  const { matchdays, teams } = data.value

  // Show top 6 + Newcastle + bottom 3
  const importantTeams = teams.filter(t => {
    const lastPos = t.positions[t.positions.length - 1]
    if (!lastPos) return false
    return lastPos <= 6 || lastPos >= 18 || t.team_name.includes('Newcastle')
  })

  const series = importantTeams.map((team, idx) => {
    const isNewcastle = team.team_name.includes('Newcastle')
    return {
      name: team.team_name.replace(' FC', '').replace(' United', ' Utd'),
      type: 'line' as const,
      data: team.positions,
      smooth: true,
      symbol: 'circle',
      symbolSize: isNewcastle ? 6 : 3,
      lineStyle: {
        width: isNewcastle ? 3 : 1.5,
        color: isNewcastle ? colors.newcastle : SERIES_COLORS[idx % SERIES_COLORS.length]
      },
      itemStyle: {
        color: isNewcastle ? colors.newcastle : SERIES_COLORS[idx % SERIES_COLORS.length]
      },
      z: isNewcastle ? 10 : 1
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      ...tooltipConfig(isDark.value)
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      textStyle: { color: colors.text, fontSize: 11 }
    },
    grid: { left: '3%', right: '4%', bottom: '60px', top: '10px', containLabel: true },
    xAxis: {
      type: 'category',
      data: matchdays.map(String),
      name: 'Matchday',
      nameLocation: 'center',
      nameGap: 25,
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } }
    },
    yAxis: {
      type: 'value',
      inverse: true,
      min: 1,
      max: 20,
      interval: 1,
      name: 'Position',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.gridLine, type: 'dashed' } },
      axisLine: { show: false }
    },
    series,
    ...CHART_ANIMATION
  }
})
</script>
