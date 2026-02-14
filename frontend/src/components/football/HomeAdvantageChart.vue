<template>
  <div class="home-advantage-chart">
    <div class="flex justify-end mb-4">
      <div class="pill-nav">
        <button
          :class="['pill-nav-item', { 'pill-nav-item-active': mode === 'current' }]"
          @click="mode = 'current'"
        >
          Current Season
        </button>
        <button
          :class="['pill-nav-item', { 'pill-nav-item-active': mode === 'multi' }]"
          @click="mode = 'multi'"
        >
          Multi-Season
        </button>
      </div>
    </div>
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading home advantage data...</div>
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
import { ref, computed, onMounted, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import type { HomeAdvantageTeam, MultiSeasonHomeAdvantage } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const mode = ref<'current' | 'multi'>('current')
const loading = ref(false)
const error = ref('')
const teams = ref<HomeAdvantageTeam[]>([])
const multiTeams = ref<MultiSeasonHomeAdvantage[]>([])

const loadCurrentData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getHomeAdvantage()
    teams.value = response.data?.teams || []
  } catch (e: any) {
    error.value = 'Failed to load home advantage data'
  } finally {
    loading.value = false
  }
}

const loadMultiSeasonData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getHomeAdvantageMultiSeason()
    multiTeams.value = response.data?.teams || []
  } catch (e: any) {
    error.value = 'Failed to load multi-season home advantage data'
  } finally {
    loading.value = false
  }
}

watch(mode, (newMode) => {
  if (newMode === 'multi' && multiTeams.value.length === 0) {
    loadMultiSeasonData()
  }
})

onMounted(loadCurrentData)

const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value

  if (mode.value === 'multi') {
    const sorted = [...multiTeams.value].sort((a, b) => b.home_advantage - a.home_advantage)
    const teamNames = sorted.map(t => t.team.replace(' FC', '').replace(' United', ' Utd'))
    const homePPG = sorted.map(t => t.avg_home_ppg)
    const awayPPG = sorted.map(t => t.avg_away_ppg)

    return {
      tooltip: {
        trigger: 'axis',
        ...tooltipConfig(isDark.value),
        formatter: (params: any) => {
          const idx = params[0].dataIndex
          const team = sorted[idx]
          return `<b>${team.team}</b><br/>
            Avg Home PPG: ${team.avg_home_ppg.toFixed(2)}<br/>
            Avg Away PPG: ${team.avg_away_ppg.toFixed(2)}<br/>
            Advantage: <b>${team.home_advantage > 0 ? '+' : ''}${team.home_advantage.toFixed(2)}</b><br/>
            Seasons: ${team.seasons_analyzed}`
        }
      },
      legend: {
        data: ['Avg Home PPG', 'Avg Away PPG'],
        top: 5,
        textStyle: { color: colors.text }
      },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '45px', containLabel: true },
      xAxis: {
        type: 'category',
        data: teamNames,
        axisLabel: { color: colors.axisLabel, rotate: 45, fontSize: 10 },
        axisLine: { lineStyle: { color: colors.axis } }
      },
      yAxis: {
        type: 'value',
        name: 'PPG',
        nameTextStyle: { color: colors.axisLabel },
        axisLabel: { color: colors.axisLabel },
        axisLine: { lineStyle: { color: colors.axis } },
        splitLine: { lineStyle: { color: colors.gridLine } }
      },
      series: [
        {
          name: 'Avg Home PPG',
          type: 'bar',
          data: homePPG,
          itemStyle: {
            color: (params: any) => {
              const team = sorted[params.dataIndex]
              return team.team.includes('Newcastle') ? colors.accent : colors.win
            }
          }
        },
        {
          name: 'Avg Away PPG',
          type: 'bar',
          data: awayPPG,
          itemStyle: {
            color: (params: any) => {
              const team = sorted[params.dataIndex]
              return team.team.includes('Newcastle') ? colors.accentViolet : colors.series[6]
            }
          }
        }
      ],
      ...CHART_ANIMATION
    }
  }

  // Current season mode
  const sorted = [...teams.value].sort((a, b) => b.advantage_index - a.advantage_index)
  const teamNames = sorted.map(t => t.team.replace(' FC', '').replace(' United', ' Utd'))
  const homePPG = sorted.map(t => t.home_ppg)
  const awayPPG = sorted.map(t => t.away_ppg)

  return {
    tooltip: {
      trigger: 'axis',
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const idx = params[0].dataIndex
        const team = sorted[idx]
        return `<b>${team.team}</b><br/>
          Home PPG: ${team.home_ppg} (${team.home_played}G: ${team.home_won}W ${team.home_drawn}D ${team.home_lost}L)<br/>
          Away PPG: ${team.away_ppg} (${team.away_played}G: ${team.away_won}W ${team.away_drawn}D ${team.away_lost}L)<br/>
          Advantage: <b>${team.advantage_index > 0 ? '+' : ''}${team.advantage_index}</b>`
      }
    },
    legend: {
      data: ['Home PPG', 'Away PPG'],
      top: 5,
      textStyle: { color: colors.text }
    },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '45px', containLabel: true },
    xAxis: {
      type: 'category',
      data: teamNames,
      axisLabel: { color: colors.axisLabel, rotate: 45, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axis } }
    },
    yAxis: {
      type: 'value',
      name: 'PPG',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } },
      splitLine: { lineStyle: { color: colors.gridLine } }
    },
    series: [
      {
        name: 'Home PPG',
        type: 'bar',
        data: homePPG,
        itemStyle: {
          color: (params: any) => {
            const team = sorted[params.dataIndex]
            return team.team.includes('Newcastle') ? colors.accent : colors.win
          }
        }
      },
      {
        name: 'Away PPG',
        type: 'bar',
        data: awayPPG,
        itemStyle: {
          color: (params: any) => {
            const team = sorted[params.dataIndex]
            return team.team.includes('Newcastle') ? colors.accentViolet : colors.series[6]
          }
        }
      }
    ],
    ...CHART_ANIMATION
  }
})
</script>
