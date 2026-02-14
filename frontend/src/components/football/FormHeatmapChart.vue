<template>
  <div class="form-heatmap-chart">
    <VChart
      :option="chartOption"
      :style="{ height: '500px', width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import { tooltipConfig, RESULT_COLORS, CHART_ANIMATION } from '@/utils/chartTheme'

const { isDark, chartColors } = useChartTheme()

interface Props {
  standings: Array<{
    position: number
    form: string
    team: {
      short_name: string
    }
  }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  const colors = chartColors.value
  const teams = props.standings
    .slice()
    .sort((a, b) => a.position - b.position)

  const heatmapData: Array<[number, number, number]> = []
  const formLabels = ['Match 1', 'Match 2', 'Match 3', 'Match 4', 'Match 5']

  teams.forEach((team, teamIndex) => {
    const formResults = team.form ? team.form.split(',').reverse() : [] // reverse to show most recent first

    formResults.forEach((result, matchIndex) => {
      let value = 0 // Loss
      if (result.trim() === 'W') value = 2 // Win
      else if (result.trim() === 'D') value = 1 // Draw

      heatmapData.push([matchIndex, teamIndex, value])
    })

    // Fill missing matches with null/0
    for (let i = formResults.length; i < 5; i++) {
      heatmapData.push([i, teamIndex, -1]) // -1 for no data
    }
  })

  const splitAreaColors = isDark.value
    ? ['rgba(40, 42, 58, 0.5)', 'rgba(40, 42, 58, 0.8)']
    : ['rgba(229, 231, 239, 0.3)', 'rgba(229, 231, 239, 0.5)']

  return {
    tooltip: {
      position: 'top',
      ...tooltipConfig(isDark.value),
      formatter: (params: any) => {
        const teamIndex = params.data[1]
        const matchIndex = params.data[0]
        const result = params.data[2]

        const teamName = teams[teamIndex]?.team.short_name || 'Unknown'
        const matchName = formLabels[matchIndex]

        let resultText = 'No Data'
        if (result === 2) resultText = 'Win'
        else if (result === 1) resultText = 'Draw'
        else if (result === 0) resultText = 'Loss'

        return `${teamName}<br/>${matchName}: ${resultText}`
      }
    },
    grid: {
      height: '80%',
      left: '100px',
      right: '50px',
      top: '10px'
    },
    xAxis: {
      type: 'category',
      data: formLabels,
      splitArea: {
        show: true,
        areaStyle: {
          color: splitAreaColors
        }
      },
      axisLabel: {
        color: colors.axisLabel,
        fontSize: 11
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'category',
      data: teams.map(team => {
        const name = team.team.short_name
        return team.team.short_name === 'Newcastle' ? `⭐ ${name}` : name
      }),
      splitArea: {
        show: true,
        areaStyle: {
          color: splitAreaColors
        }
      },
      axisLabel: {
        color: colors.axisLabel,
        fontSize: 11,
        formatter: (value: string) => {
          return value.length > 12 ? value.substring(0, 12) + '...' : value
        }
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    visualMap: {
      min: -1,
      max: 2,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      pieces: [
        { value: -1, color: colors.axis, label: 'No Data' },
        { value: 0, color: RESULT_COLORS.loss, label: 'Loss' },
        { value: 1, color: RESULT_COLORS.draw, label: 'Draw' },
        { value: 2, color: RESULT_COLORS.win, label: 'Win' }
      ],
      textStyle: {
        color: colors.axisLabel,
        fontSize: 11
      }
    },
    series: [{
      name: 'Form',
      type: 'heatmap',
      data: heatmapData,
      label: {
        show: true,
        color: '#fff',
        fontSize: 10,
        fontWeight: 'bold',
        formatter: (params: any) => {
          const result = params.data[2]
          if (result === -1) return ''
          if (result === 2) return 'W'
          if (result === 1) return 'D'
          if (result === 0) return 'L'
          return ''
        }
      },
      emphasis: {
        itemStyle: {
          borderColor: colors.tooltipText,
          borderWidth: 1
        }
      }
    }],
    ...CHART_ANIMATION
  }
})
</script>
