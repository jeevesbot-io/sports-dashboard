import { computed } from 'vue'
import { useTheme } from './useTheme'

export function useChartTheme() {
  const { isDark } = useTheme()

  const chartColors = computed(() => ({
    bg: 'transparent',
    text: isDark.value ? '#b0b2c3' : '#3b3d50',
    textMuted: isDark.value ? '#555770' : '#8b8da3',
    axis: isDark.value ? '#282a3a' : '#e5e7ef',
    axisLabel: isDark.value ? '#8b8da3' : '#555770',
    tooltipBg: isDark.value ? 'rgba(22, 24, 34, 0.95)' : 'rgba(255, 255, 255, 0.95)',
    tooltipBorder: isDark.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
    tooltipText: isDark.value ? '#f4f5f8' : '#0f1117',
    gridLine: isDark.value ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)',
    series: [
      '#06b6d4', // cyan
      '#8b5cf6', // violet
      '#f59e0b', // amber
      '#ef4444', // red
      '#10b981', // emerald
      '#ec4899', // pink
      '#3b82f6', // blue
      '#f97316', // orange
    ],
    win: '#10b981',
    draw: '#f59e0b',
    loss: '#ef4444',
    accent: '#06b6d4',
    accentViolet: '#8b5cf6',
    newcastle: '#c8a84e',
  }))

  const baseChartConfig = computed(() => ({
    tooltip: {
      backgroundColor: chartColors.value.tooltipBg,
      borderColor: chartColors.value.tooltipBorder,
      borderWidth: 1,
      textStyle: {
        color: chartColors.value.tooltipText,
        fontFamily: 'Inter, sans-serif',
        fontSize: 13,
      },
      extraCssText: 'backdrop-filter: blur(12px); border-radius: 10px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); padding: 10px 14px;',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      axisLine: { lineStyle: { color: chartColors.value.axis } },
      axisTick: { show: false },
      axisLabel: {
        color: chartColors.value.axisLabel,
        fontFamily: 'Inter, sans-serif',
        fontSize: 11,
      },
      splitLine: { show: false },
    },
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: chartColors.value.axisLabel,
        fontFamily: 'Inter, sans-serif',
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: chartColors.value.gridLine,
          type: 'dashed' as const,
        },
      },
    },
    legend: {
      textStyle: {
        color: chartColors.value.text,
        fontFamily: 'Inter, sans-serif',
        fontSize: 12,
      },
    },
    animationDuration: 800,
    animationEasing: 'cubicOut' as const,
  }))

  return {
    isDark,
    chartColors,
    baseChartConfig,
  }
}
