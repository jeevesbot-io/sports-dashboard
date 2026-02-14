/**
 * Shared ECharts theme configuration.
 * All chart components should use useChartTheme() composable instead of hardcoding colors.
 * This file provides helper functions for common chart patterns.
 */

export const CHART_ANIMATION = {
  animationDuration: 800,
  animationEasing: 'cubicOut' as const,
  animationDelay: (idx: number) => idx * 50,
}

export const SERIES_COLORS = [
  '#06b6d4', // cyan
  '#8b5cf6', // violet
  '#f59e0b', // amber
  '#ef4444', // red
  '#10b981', // emerald
  '#ec4899', // pink
  '#3b82f6', // blue
  '#f97316', // orange
]

export const RESULT_COLORS = {
  win: '#10b981',
  draw: '#f59e0b',
  loss: '#ef4444',
}

export function tooltipConfig(isDark: boolean) {
  return {
    backgroundColor: isDark ? 'rgba(22, 24, 34, 0.95)' : 'rgba(255, 255, 255, 0.95)',
    borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
    borderWidth: 1,
    textStyle: {
      color: isDark ? '#f4f5f8' : '#0f1117',
      fontFamily: 'Inter, sans-serif',
      fontSize: 13,
    },
    extraCssText: 'backdrop-filter: blur(12px); border-radius: 10px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); padding: 10px 14px;',
  }
}

export function axisConfig(isDark: boolean) {
  const axisColor = isDark ? '#282a3a' : '#e5e7ef'
  const labelColor = isDark ? '#8b8da3' : '#555770'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)'

  return {
    xAxis: {
      axisLine: { lineStyle: { color: axisColor } },
      axisTick: { show: false },
      axisLabel: { color: labelColor, fontFamily: 'Inter, sans-serif', fontSize: 11 },
      splitLine: { show: false },
    },
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: labelColor, fontFamily: 'Inter, sans-serif', fontSize: 11 },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' as const } },
    },
  }
}

export function legendConfig(isDark: boolean) {
  return {
    textStyle: {
      color: isDark ? '#b0b2c3' : '#3b3d50',
      fontFamily: 'Inter, sans-serif',
      fontSize: 12,
    },
  }
}
