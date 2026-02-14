<!--
xG Scatter Chart Component - Actual vs Expected Goals
-->
<template>
  <div class="xg-chart">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-96">
      <ProgressSpinner />
    </div>

    <!-- Chart -->
    <div v-else-if="chartData.length > 0" class="chart-container">
      <div ref="chartRef" class="w-full h-96"></div>
      
      <!-- Chart Info -->
      <div class="mt-3 p-2 bg-gray-50 rounded text-xs">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <i class="pi pi-info-circle text-blue-500 mr-1"></i>
            <strong>Diagonal line:</strong> Perfect xG performance
          </div>
          <div>
            <i class="pi pi-arrow-up text-green-500 mr-1"></i>
            <strong>Above line:</strong> Overperforming xG (scoring more than expected)
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div 
      v-else 
      class="flex flex-col items-center justify-center h-96 text-gray-500"
    >
      <i class="pi pi-chart-scatter text-4xl mb-3"></i>
      <p>No xG data available for chart</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

// PrimeVue Components
import ProgressSpinner from 'primevue/progressspinner'

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

// Reactive state
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

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
  if (overperformance > 3) return '#16a34a' // Green - significant overperformance
  if (overperformance > 1) return '#2563eb' // Blue - slight overperformance
  if (overperformance > -1) return '#64748b' // Gray - neutral
  if (overperformance > -3) return '#f97316' // Orange - slight underperformance
  return '#dc2626' // Red - significant underperformance
}

const createChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option = {
    title: {
      text: 'Goals vs Expected Goals',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const team = chartData.value.find(t => t.team === params.data.name)
        if (!team) return ''
        
        return `
          <div class="p-2">
            <div class="font-bold mb-1">${team.team}</div>
            <div class="text-sm space-y-1">
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
      top: '15%'
    },
    xAxis: {
      type: 'value',
      name: 'Expected Goals (xG)',
      nameLocation: 'center',
      nameGap: 30,
      min: 0,
      max: maxValue.value,
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: 'Actual Goals',
      nameLocation: 'center',
      nameGap: 40,
      min: 0,
      max: maxValue.value,
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
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
          color: '#9ca3af',
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
            borderColor: '#374151',
            borderWidth: 2
          }
        },
        z: 10
      }
    ],
    legend: {
      show: false
    },
    animation: true,
    animationDuration: 1000
  }

  chartInstance.setOption(option)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// Watchers
watch(
  () => [chartData.value, maxValue.value],
  () => {
    if (chartInstance && chartData.value.length > 0) {
      createChart()
    }
  },
  { deep: true }
)

// Lifecycle
onMounted(() => {
  if (chartData.value.length > 0) {
    createChart()
  }
  
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})
</script>

<style scoped>
.xg-chart {
  @apply w-full;
}

.chart-container {
  @apply w-full;
}

:deep(.echarts-tooltip) {
  @apply shadow-lg border-gray-200;
}
</style>