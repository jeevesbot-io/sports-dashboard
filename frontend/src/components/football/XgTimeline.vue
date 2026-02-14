<template>
  <div class="xg-timeline">
    <div class="flex items-center mb-3">
      <label class="text-sm text-[var(--sd-text-muted)] mr-2">Team:</label>
      <Dropdown
        v-model="selectedTeamId"
        :options="teamOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Select a team"
        class="w-64"
        @change="loadTimeline"
      />
    </div>

    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading xG timeline...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <div v-else-if="!timeline.length" class="text-center py-8 text-[var(--sd-text-muted)]">
      Select a team to view their xG timeline.
    </div>
    <VChart
      v-show="!loading && !error && timeline.length > 0"
      :option="chartOption"
      :style="{ height: '400px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import apiClient from '@/api'
import { useFootballStore } from '@/stores/football'
import type { XGTimelinePoint } from '@/types'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

const store = useFootballStore()
const loading = ref(false)
const error = ref('')
const selectedTeamId = ref<number | null>(null)
const timeline = ref<XGTimelinePoint[]>([])
const teamName = ref('')

const teamOptions = computed(() => {
  return store.standings.map((s: any) => ({
    label: s.team.short_name || s.team.name,
    value: s.team.id
  }))
})

const loadTimeline = async () => {
  if (!selectedTeamId.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getTeamXGTimeline(selectedTeamId.value)
    const data = response.data
    if (data) {
      timeline.value = data.timeline || []
      teamName.value = data.team?.short_name || data.team?.name || ''
    }
  } catch (e: any) {
    error.value = 'Failed to load xG timeline'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Auto-select Newcastle if available
  const newcastle = store.standings.find((s: any) => s.team?.short_name === 'Newcastle')
  if (newcastle) {
    selectedTeamId.value = newcastle.team.id
    loadTimeline()
  }
})

const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value
  const matchdays = timeline.value.map(t => t.matchday)
  const cumGoals = timeline.value.map(t => t.cumulative_goals)
  const cumXG = timeline.value.map(t => t.cumulative_xg)
  const cumGA = timeline.value.map(t => t.cumulative_goals_against)
  const cumXGA = timeline.value.map(t => t.cumulative_xg_against)

  return {
    tooltip: {
      trigger: 'axis',
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex
        if (idx === undefined) return ''
        const t = timeline.value[idx]
        return `<b>Match ${t.matchday}</b> ${t.is_home ? '(H)' : '(A)'} vs ${t.opponent}<br/>
          Goals: ${t.goals_for}-${t.goals_against} | xG: ${t.xg_for}-${t.xg_against}<br/>
          Cumulative G: ${t.cumulative_goals} | xG: ${t.cumulative_xg}<br/>
          Cumulative GA: ${t.cumulative_goals_against} | xGA: ${t.cumulative_xg_against}`
      }
    },
    legend: {
      data: ['Actual Goals', 'Expected Goals (xG)', 'Goals Against', 'xG Against'],
      top: 0,
      textStyle: { color: colors.text, fontSize: 10 }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: {
      type: 'category',
      data: matchdays,
      name: 'Match',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } }
    },
    yAxis: {
      type: 'value',
      name: 'Cumulative',
      nameTextStyle: { color: colors.axisLabel },
      axisLabel: { color: colors.axisLabel },
      axisLine: { lineStyle: { color: colors.axis } },
      splitLine: { lineStyle: { color: colors.gridLine } }
    },
    series: [
      {
        name: 'Actual Goals',
        type: 'line',
        data: cumGoals,
        lineStyle: { width: 3, color: colors.win },
        itemStyle: { color: colors.win },
        areaStyle: { color: `${colors.win}1a` },
        smooth: true
      },
      {
        name: 'Expected Goals (xG)',
        type: 'line',
        data: cumXG,
        lineStyle: { width: 2, color: colors.win, type: 'dashed' },
        itemStyle: { color: colors.win },
        smooth: true
      },
      {
        name: 'Goals Against',
        type: 'line',
        data: cumGA,
        lineStyle: { width: 3, color: colors.loss },
        itemStyle: { color: colors.loss },
        areaStyle: { color: `${colors.loss}1a` },
        smooth: true
      },
      {
        name: 'xG Against',
        type: 'line',
        data: cumXGA,
        lineStyle: { width: 2, color: colors.loss, type: 'dashed' },
        itemStyle: { color: colors.loss },
        smooth: true
      }
    ],
    ...CHART_ANIMATION
  }
})
</script>
