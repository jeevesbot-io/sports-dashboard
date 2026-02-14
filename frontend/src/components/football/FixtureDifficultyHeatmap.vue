<template>
  <div class="fixture-difficulty-heatmap">
    <div class="flex gap-2 mb-4">
      <button
        :class="['pill-nav-item', { 'pill-nav-item-active': mode === 'team_rating' }]"
        @click="mode = 'team_rating'; loadData()"
      >Team Rating</button>
      <button
        :class="['pill-nav-item', { 'pill-nav-item-active': mode === 'current_form' }]"
        @click="mode = 'current_form'; loadData()"
      >Current Form</button>
    </div>
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading fixture difficulty...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <VChart
      v-show="!loading && !error && data"
      :option="chartOption"
      :style="{ height: chartHeight, width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import type { FixtureDifficultyResponse } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const loading = ref(false)
const error = ref('')
const data = ref<FixtureDifficultyResponse | null>(null)
const mode = ref('team_rating')

const chartHeight = computed(() => {
  const teamCount = data.value?.teams.length || 20
  return `${Math.max(400, teamCount * 28)}px`
})

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getFixtureDifficulty(2025, mode.value)
    data.value = response.data || null
  } catch (e: any) {
    error.value = 'Failed to load fixture difficulty data'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const chartOption = computed<EChartsOption>(() => {
  if (!data.value) return {}
  const colors = chartColors.value
  const teams = data.value.teams
  const teamNames = teams.map(t => t.tla)

  // Find max matchday
  const maxMatchday = Math.max(...teams.flatMap(t => t.fixtures.map(f => f.matchday)))
  const matchdays = Array.from({ length: maxMatchday }, (_, i) => i + 1)

  // Build heatmap data: [matchdayIndex, teamIndex, difficulty]
  const heatmapData: any[] = []
  const cellLabels: Record<string, { short: string; isHome: boolean; result: string | null; status: string }> = {}

  teams.forEach((team, teamIdx) => {
    team.fixtures.forEach(fix => {
      const mdIdx = fix.matchday - 1
      heatmapData.push([mdIdx, teamIdx, fix.difficulty])
      cellLabels[`${mdIdx}-${teamIdx}`] = {
        short: fix.opponent_short,
        isHome: fix.is_home,
        result: fix.result || null,
        status: fix.status
      }
    })
  })

  return {
    tooltip: {
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const [mdIdx, teamIdx, difficulty] = params.data
        const key = `${mdIdx}-${teamIdx}`
        const cell = cellLabels[key]
        if (!cell) return ''
        const venue = cell.isHome ? 'Home' : 'Away'
        const resultStr = cell.result ? ` (${cell.result})` : ''
        return `<b>${teamNames[teamIdx]}</b> vs ${cell.short} (${venue})${resultStr}<br/>Difficulty: <b>${(difficulty * 100).toFixed(0)}%</b>`
      }
    },
    grid: { left: '60px', right: '60px', bottom: '40px', top: '30px' },
    xAxis: {
      type: 'category',
      data: matchdays.map(String),
      name: 'Matchday',
      nameLocation: 'center',
      nameGap: 25,
      axisLabel: { color: colors.axisLabel, fontSize: 9 },
      axisLine: { lineStyle: { color: colors.axis } },
      splitArea: { show: false }
    },
    yAxis: {
      type: 'category',
      data: teamNames,
      axisLabel: { color: colors.axisLabel, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axis } }
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      top: 0,
      itemWidth: 12,
      itemHeight: 120,
      textStyle: { color: colors.text },
      inRange: {
        color: ['#10b981', '#f59e0b', '#ef4444']
      }
    },
    series: [{
      type: 'heatmap',
      data: heatmapData,
      label: {
        show: true,
        fontSize: 8,
        color: isDark.value ? '#ddd' : '#333',
        formatter: (params: any) => {
          const [mdIdx, teamIdx] = params.data
          const key = `${mdIdx}-${teamIdx}`
          const cell = cellLabels[key]
          if (!cell) return ''
          if (cell.status === 'FINISHED' && cell.result) {
            return `{${cell.result === 'W' ? 'win' : cell.result === 'L' ? 'loss' : 'draw'}|${cell.result}}`
          }
          return cell.short
        },
        rich: {
          win: { color: '#10b981', fontWeight: 'bold', fontSize: 9 },
          draw: { color: '#f59e0b', fontWeight: 'bold', fontSize: 9 },
          loss: { color: '#ef4444', fontWeight: 'bold', fontSize: 9 }
        }
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      },
      itemStyle: {
        borderColor: isDark.value ? '#1a1c2e' : '#fff',
        borderWidth: 1
      }
    }],
    ...CHART_ANIMATION
  }
})
</script>
