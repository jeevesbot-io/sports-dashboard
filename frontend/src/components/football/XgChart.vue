<!--
xG Scatter Chart Component - Actual vs Expected Goals
-->
<template>
  <div class="xg-chart">
    <!-- Chart -->
    <div v-if="chartData.length > 0">
      <VChart
        :option="chartOption"
        :style="{ height: '384px', width: '100%' }"
        autoresize
      />

      <!-- Chart Info -->
      <div class="mt-3 p-2 rounded text-xs bg-[var(--sd-surface-100)] border border-[var(--sd-glass-border)]">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-[var(--sd-text-muted)]">
          <div>
            <i class="pi pi-info-circle text-[var(--sd-accent)] mr-1"></i>
            <strong class="text-[var(--sd-text-primary)]">Diagonal line:</strong> Perfect xG performance
          </div>
          <div>
            <i class="pi pi-arrow-up mr-1" style="color: #10b981"></i>
            <strong class="text-[var(--sd-text-primary)]">Above line:</strong> Overperforming xG (scoring more than expected)
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="flex flex-col items-center justify-center h-96 text-[var(--sd-text-muted)]"
    >
      <i class="pi pi-chart-scatter text-4xl mb-3"></i>
      <p>No xG data available for chart</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

// Types
interface XGChartData {
  team: string
  matches: number
  xg_for: number
  xg_against: number
  xg_diff: number
  goals_for: number
  goals_against: number
  goal_diff: number
  overperformance: number
}

// Props
interface Props {
  data: XGChartData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Computed properties
const chartData = computed(() => props.data || [])

const scatterData = computed(() => {
  return chartData.value.map(team => ({
    name: team.team,
    value: [team.xg_for, team.goals_for],
    itemStyle: {
      color: getTeamColor(team.overperformance)
    }
  }))
})

const maxValue = computed(() => {
  if (!chartData.value.length) return 50

  const maxXG = Math.max(...chartData.value.map(t => t.xg_for))
  const maxGoals = Math.max(...chartData.value.map(t => t.goals_for))
  return Math.ceil(Math.max(maxXG, maxGoals) * 1.1)
})

// Methods
const getTeamColor = (overperformance: number): string => {
  const colors = chartColors.value
  if (overperformance > 3) return colors.win        // Green - significant overperformance
  if (overperformance > 1) return colors.series[6]  // Blue - slight overperformance (#3b82f6)
  if (overperformance > -1) return colors.axisLabel  // Muted - neutral
  if (overperformance > -3) return colors.series[7]  // Orange - slight underperformance (#f97316)
  return colors.loss                                  // Red - significant underperformance
}

// Chart option
const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value

  return {
    tooltip: {
      trigger: 'item',
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const team = chartData.value.find(t => t.team === params.data.name)
        if (!team) return ''

        return `
          <div style="padding: 2px;">
            <div style="font-weight: bold; margin-bottom: 4px;">${team.team}</div>
            <div style="font-size: 12px;">
              <div>xG: ${team.xg_for.toFixed(1)} | Goals: ${team.goals_for}</div>
              <div>Over/Under: ${team.overperformance > 0 ? '+' : ''}${team.overperformance.toFixed(1)}</div>
              <div>Matches: ${team.matches}</div>
            </div>
          </div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'value',
      name: 'Expected Goals (xG)',
      nameLocation: 'center',
      nameGap: 30,
      nameTextStyle: { color: colors.axisLabel },
      min: 0,
      max: maxValue.value,
      axisLine: {
        lineStyle: {
          color: colors.axis
        }
      },
      axisLabel: {
        color: colors.axisLabel
      },
      splitLine: {
        lineStyle: {
          color: colors.gridLine,
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: 'Actual Goals',
      nameLocation: 'center',
      nameGap: 40,
      nameTextStyle: { color: colors.axisLabel },
      min: 0,
      max: maxValue.value,
      axisLine: {
        lineStyle: {
          color: colors.axis
        }
      },
      axisLabel: {
        color: colors.axisLabel
      },
      splitLine: {
        lineStyle: {
          color: colors.gridLine,
          type: 'dashed'
        }
      }
    },
    series: [
      // Diagonal reference line (perfect xG performance)
      {
        type: 'line',
        name: 'Perfect xG Performance',
        data: [[0, 0], [maxValue.value, maxValue.value]],
        lineStyle: {
          color: colors.textMuted,
          width: 2,
          type: 'dashed'
        },
        symbol: 'none',
        silent: true,
        z: 0
      },
      // Scatter plot of teams
      {
        type: 'scatter',
        name: 'Teams',
        data: scatterData.value,
        symbolSize: 8,
        emphasis: {
          symbolSize: 12,
          itemStyle: {
            borderColor: colors.text,
            borderWidth: 2
          }
        },
        z: 10
      }
    ],
    legend: {
      show: false
    },
    ...CHART_ANIMATION
  }
})
</script>
