<template>
  <div class="team-vs-league">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading comparison...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <div v-else-if="!metrics.length" class="text-center py-8 text-[var(--sd-text-muted)]">No comparison data available.</div>
    <div v-show="!loading && !error && metrics.length" class="flex flex-col lg:flex-row gap-4">
      <!-- Radar Chart -->
      <div class="flex-1">
        <VChart
          :option="radarOption"
          :style="{ height: '350px', width: '100%' }"
          autoresize
        />
      </div>
      <!-- Stat Cards -->
      <div class="flex-1 flex flex-col gap-2">
        <div
          v-for="m in metrics"
          :key="m.metric"
          class="flex justify-between items-center px-3 py-2.5 rounded-lg bg-[var(--sd-surface-100)] border border-[var(--sd-glass-border)]"
        >
          <div class="text-sm text-[var(--sd-text-muted)]">{{ m.metric }}</div>
          <div class="flex gap-1.5 items-center text-sm">
            <span
              class="font-bold"
              :class="m.difference > 0 ? 'text-[var(--sd-win)]' : m.difference < 0 ? 'text-[var(--sd-loss)]' : 'text-[var(--sd-text-primary)]'"
            >
              {{ m.team_value }}
            </span>
            <span class="text-xs text-[var(--sd-text-muted)]">vs</span>
            <span class="text-[var(--sd-text-secondary)]">{{ m.league_value }}</span>
            <span
              class="text-xs"
              :class="m.difference > 0 ? 'text-[var(--sd-win)]' : m.difference < 0 ? 'text-[var(--sd-loss)]' : 'text-[var(--sd-text-muted)]'"
            >
              ({{ m.difference > 0 ? '+' : '' }}{{ m.difference }})
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import { useFootballStore } from '@/stores/football'
import type { TeamVsLeagueMetric } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const store = useFootballStore()
const loading = ref(false)
const error = ref('')
const metrics = ref<TeamVsLeagueMetric[]>([])

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    // Find Newcastle's team ID
    const standings = store.standings
    const newcastle = standings.find((s: any) => s.team?.short_name === 'Newcastle')
    if (!newcastle) {
      error.value = 'Newcastle not found in standings'
      return
    }

    const response = await apiClient.getTeamVsLeague(newcastle.team.id)
    metrics.value = response.data?.metrics || []
  } catch (e: any) {
    error.value = 'Failed to load comparison data'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const radarOption = computed<EChartsOption>(() => {
  const colors = chartColors.value

  // Normalize values for radar display
  const indicators = metrics.value.map(m => {
    const rawMax = Math.max(m.team_value, m.league_value) * 1.3
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawMax || 1)))
    const niceMax = Math.ceil(rawMax / magnitude) * magnitude
    return {
      name: m.metric.replace(' / Game', '/G').replace('Points Per Game', 'PPG'),
      max: Math.max(niceMax, 1)
    }
  })

  const splitAreaColors = isDark.value
    ? ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.04)']
    : ['rgba(0,0,0,0.01)', 'rgba(0,0,0,0.03)']

  return {
    tooltip: {
      ...tooltipConfig(isDark.value)
    },
    legend: {
      data: ['Newcastle', 'League Avg'],
      bottom: 0,
      textStyle: { color: colors.text }
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitArea: { areaStyle: { color: splitAreaColors } },
      axisLine: { lineStyle: { color: colors.axis } },
      splitLine: { lineStyle: { color: colors.axis } },
      axisName: { color: colors.axisLabel, fontSize: 11 }
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: metrics.value.map(m => m.team_value),
          name: 'Newcastle',
          lineStyle: { color: colors.accent, width: 2 },
          areaStyle: { color: `${colors.accent}26` },
          itemStyle: { color: colors.accent }
        },
        {
          value: metrics.value.map(m => m.league_value),
          name: 'League Avg',
          lineStyle: { color: colors.textMuted, width: 1, type: 'dashed' },
          areaStyle: { color: `${colors.textMuted}1a` },
          itemStyle: { color: colors.textMuted }
        }
      ]
    }],
    ...CHART_ANIMATION
  }
})
</script>
