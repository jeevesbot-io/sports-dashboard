<template>
  <div class="goals-comparison-chart">
    <h3>Goals Comparison</h3>
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
    title: {
      text: 'Goals For vs Goals Against',
      left: 'center',
      textStyle: {
        color: '#f0f0f0',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: '#1a1a1a',
      borderColor: '#333',
      textStyle: {
        color: '#f0f0f0'
      },
      formatter: (params: any) => {
        const team = params[0].name
        const goalsFor = Math.abs(params[1]?.value || 0)
        const goalsAgainst = Math.abs(params[0]?.value || 0)
        const difference = goalsFor - goalsAgainst
        return `
          <div style="padding: 8px;">
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
      top: 30,
      textStyle: {
        color: '#888'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '80px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#888',
        formatter: (value: number) => Math.abs(value).toString()
      },
      axisLine: {
        lineStyle: {
          color: '#333'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#222'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: {
        color: '#888',
        formatter: (value: string) => {
          return data.find(d => d.name === value)?.isNewcastle 
            ? `⭐ ${value}` 
            : value
        }
      },
      axisLine: {
        lineStyle: {
          color: '#333'
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
            color: d.isNewcastle ? '#ff6b6b' : '#e74c3c'
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
            color: d.isNewcastle ? '#4ecdc4' : '#27ae60'
          }
        })),
        emphasis: {
          focus: 'series'
        }
      }
    ]
  }
})
</script>

<style scoped>
.goals-comparison-chart h3 {
  margin: 0 0 1rem 0;
  color: #f0f0f0;
  font-size: 1.1rem;
  text-align: center;
}
</style>