<template>
  <div class="points-progression-chart">
    <h3>Points Progression - Top 6 Teams</h3>
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
    points: number
    played: number
    team: {
      short_name: string
    }
  }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  // For now, create a simple visualization using current points and games played
  // This would be replaced with actual matchday-by-matchday data from backend
  const top6Teams = props.standings.slice(0, 6)
  const newcastleInTop6 = top6Teams.find(t => t.team.short_name === 'Newcastle')
  
  // If Newcastle isn't in top 6, include them
  let teamsToShow = [...top6Teams]
  if (!newcastleInTop6) {
    const newcastle = props.standings.find(t => t.team.short_name === 'Newcastle')
    if (newcastle) {
      teamsToShow.push(newcastle)
    }
  }

  // Generate simplified progression data (this would come from API in real implementation)
  const maxMatchday = Math.max(...props.standings.map(s => s.played))
  const matchdays = Array.from({ length: maxMatchday }, (_, i) => i + 1)
  
  const series = teamsToShow.map(team => {
    const isNewcastle = team.team.short_name === 'Newcastle'
    
    // Simplified: assume linear progression (in reality would be actual match results)
    const pointsPerGame = team.points / team.played
    const progressionData = matchdays.map(matchday => {
      if (matchday > team.played) return null
      return Math.round(pointsPerGame * matchday)
    })

    return {
      name: team.team.short_name,
      type: 'line',
      data: progressionData,
      lineStyle: {
        width: isNewcastle ? 4 : 2,
        color: isNewcastle ? '#f0f0f0' : undefined
      },
      itemStyle: {
        color: isNewcastle ? '#f0f0f0' : undefined
      },
      emphasis: {
        lineStyle: {
          width: isNewcastle ? 5 : 3
        }
      },
      smooth: true,
      connectNulls: false
    }
  })

  return {
    title: {
      text: 'Cumulative Points Over Season',
      left: 'center',
      textStyle: {
        color: '#f0f0f0',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a1a1a',
      borderColor: '#333',
      textStyle: {
        color: '#f0f0f0'
      },
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: '#666'
        }
      }
    },
    legend: {
      data: teamsToShow.map(t => t.team.short_name),
      top: 35,
      textStyle: {
        color: '#888'
      },
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '80px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: matchdays,
      name: 'Matchday',
      nameTextStyle: {
        color: '#888'
      },
      axisLabel: {
        color: '#888'
      },
      axisLine: {
        lineStyle: {
          color: '#333'
        }
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: 'Points',
      nameTextStyle: {
        color: '#888'
      },
      axisLabel: {
        color: '#888'
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
    series: series
  }
})
</script>

<style scoped>
.points-progression-chart h3 {
  margin: 0 0 1rem 0;
  color: #f0f0f0;
  font-size: 1.1rem;
  text-align: center;
}
</style>