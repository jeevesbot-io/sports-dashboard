<template>
  <div class="goals-comparison-chart">
    <VChart
      :option="chartOption"
      :style="{ height: '400px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

interface Props {
  standings: Array<{
    position: number
    goals_for: number
    goals_against: number
    goal_difference: number
    team: {
      short_name: string
    }
  }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value
  const data = props.standings
    .slice()
    .sort((a, b) => b.goal_difference - a.goal_difference)
    .map(team => ({
      name: team.team.short_name,
      goalsFor: team.goals_for,
      goalsAgainst: -team.goals_against, // negative for left side
      isNewcastle: team.team.short_name === 'Newcastle'
    }))

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const team = params[0].name
        const goalsFor = Math.abs(params[1]?.value || 0)
        const goalsAgainst = Math.abs(params[0]?.value || 0)
        const difference = goalsFor - goalsAgainst
        return `
          <div style="padding: 4px;">
            <strong>${team}</strong><br/>
            Goals For: ${goalsFor}<br/>
            Goals Against: ${goalsAgainst}<br/>
            Difference: ${difference > 0 ? '+' : ''}${difference}
          </div>
        `
      }
    },
    legend: {
      data: ['Goals Against', 'Goals For'],
      top: 5,
      textStyle: {
        color: colors.text
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '45px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: colors.axisLabel,
        formatter: (value: number) => Math.abs(value).toString()
      },
      axisLine: {
        lineStyle: {
          color: colors.axis
        }
      },
      splitLine: {
        lineStyle: {
          color: colors.gridLine
        }
      }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: {
        color: colors.axisLabel,
        formatter: (value: string) => {
          return data.find(d => d.name === value)?.isNewcastle
            ? `⭐ ${value}`
            : value
        }
      },
      axisLine: {
        lineStyle: {
          color: colors.axis
        }
      },
      axisTick: {
        show: false
      }
    },
    series: [
      {
        name: 'Goals Against',
        type: 'bar',
        stack: 'total',
        data: data.map(d => ({
          value: d.goalsAgainst,
          itemStyle: {
            color: d.isNewcastle ? colors.accentViolet : colors.loss
          }
        })),
        emphasis: {
          focus: 'series'
        }
      },
      {
        name: 'Goals For',
        type: 'bar',
        stack: 'total',
        data: data.map(d => ({
          value: d.goalsFor,
          itemStyle: {
            color: d.isNewcastle ? colors.accent : colors.win
          }
        })),
        emphasis: {
          focus: 'series'
        }
      }
    ],
    ...CHART_ANIMATION
  }
})
</script>
