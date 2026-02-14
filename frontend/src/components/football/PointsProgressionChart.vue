<template>
  <div class="points-progression-chart">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading chart data...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <VChart
      v-show="!loading && !error"
      :option="chartOption"
      :style="{ height: (height || 400) + 'px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

interface Props {
  useApi?: boolean
  standings?: Array<{
    position: number
    points: number
    played: number
    team: {
      short_name: string
    }
  }>
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  useApi: true,
  standings: () => [],
  height: 400
})

const emit = defineEmits<{
  error: [error: any]
}>()

const loading = ref(false)
const error = ref('')
const apiMatchdays = ref<number[]>([])
const apiSeries = ref<any[]>([])

const loadFromApi = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getPointsProgression()
    const data = response.data
    if (data) {
      apiMatchdays.value = data.matchdays || []
      apiSeries.value = data.series || []
    }
  } catch (e: any) {
    error.value = 'Failed to load points progression data'
    emit('error', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.useApi) {
    loadFromApi()
  }
})

watch(() => props.useApi, (val) => {
  if (val) loadFromApi()
})

const chartOption = computed<EChartsOption>(() => {
  if (props.useApi && apiSeries.value.length > 0) {
    return buildApiChart()
  }
  return buildStandingsChart()
})

function buildApiChart(): EChartsOption {
  // Select top 6 by final points + always include Newcastle
  const sorted = [...apiSeries.value].sort((a, b) => {
    const aLast = a.data?.length ? a.data[a.data.length - 1]?.points ?? 0 : 0
    const bLast = b.data?.length ? b.data[b.data.length - 1]?.points ?? 0 : 0
    return bLast - aLast
  })

  const top6 = sorted.slice(0, 6)
  const newcastleInTop6 = top6.some((s: any) =>
    s.name === 'Newcastle United' || s.name === 'Newcastle'
  )

  let teamsToShow = [...top6]
  if (!newcastleInTop6) {
    const newcastle = sorted.find((s: any) =>
      s.name === 'Newcastle United' || s.name === 'Newcastle'
    )
    if (newcastle) teamsToShow.push(newcastle)
  }

  const seriesColors = chartColors.value.series
  let colorIdx = 0

  const series = teamsToShow.map((team: any) => {
    const isNewcastle = team.name === 'Newcastle United' || team.name === 'Newcastle'
    const pointsData = (team.data || []).map((d: any) => d.points ?? d)
    const color = isNewcastle ? chartColors.value.accent : seriesColors[colorIdx++ % seriesColors.length]

    return {
      name: team.name,
      type: 'line',
      data: pointsData,
      lineStyle: {
        width: isNewcastle ? 4 : 2,
        color
      },
      itemStyle: { color },
      emphasis: {
        lineStyle: { width: isNewcastle ? 5 : 3 }
      },
      smooth: true,
      connectNulls: false
    }
  })

  return buildChartConfig(
    apiMatchdays.value,
    teamsToShow.map((t: any) => t.name),
    series
  )
}

function buildStandingsChart(): EChartsOption {
  const top6Teams = props.standings.slice(0, 6)
  const newcastleInTop6 = top6Teams.find(t => t.team.short_name === 'Newcastle')

  let teamsToShow = [...top6Teams]
  if (!newcastleInTop6) {
    const newcastle = props.standings.find(t => t.team.short_name === 'Newcastle')
    if (newcastle) teamsToShow.push(newcastle)
  }

  const maxMatchday = Math.max(...props.standings.map(s => s.played), 1)
  const matchdays = Array.from({ length: maxMatchday }, (_, i) => i + 1)

  const seriesColors = chartColors.value.series
  let colorIdx = 0

  const series = teamsToShow.map(team => {
    const isNewcastle = team.team.short_name === 'Newcastle'
    const pointsPerGame = team.played > 0 ? team.points / team.played : 0
    const progressionData = matchdays.map(matchday => {
      if (matchday > team.played) return null
      return Math.round(pointsPerGame * matchday)
    })
    const color = isNewcastle ? chartColors.value.accent : seriesColors[colorIdx++ % seriesColors.length]

    return {
      name: team.team.short_name,
      type: 'line',
      data: progressionData,
      lineStyle: {
        width: isNewcastle ? 4 : 2,
        color
      },
      itemStyle: { color },
      emphasis: {
        lineStyle: { width: isNewcastle ? 5 : 3 }
      },
      smooth: true,
      connectNulls: false
    }
  })

  return buildChartConfig(
    matchdays,
    teamsToShow.map(t => t.team.short_name),
    series
  )
}

function buildChartConfig(matchdays: number[], teamNames: string[], series: any[]): EChartsOption {
  return {
    tooltip: {
      trigger: 'axis',
      ...tooltipConfig(isDark.value),
      axisPointer: { type: 'line', lineStyle: { color: chartColors.value.axis } }
    },
    legend: {
      data: teamNames,
      top: 5,
      textStyle: { color: chartColors.value.text },
      type: 'scroll'
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', top: '50px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: matchdays,
      name: 'Matchday',
      nameTextStyle: { color: chartColors.value.axisLabel },
      axisLabel: { color: chartColors.value.axisLabel },
      axisLine: { lineStyle: { color: chartColors.value.axis } },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'Points',
      nameTextStyle: { color: chartColors.value.axisLabel },
      axisLabel: { color: chartColors.value.axisLabel },
      axisLine: { lineStyle: { color: chartColors.value.axis } },
      splitLine: { lineStyle: { color: chartColors.value.gridLine } }
    },
    series,
    ...CHART_ANIMATION
  }
}
</script>
