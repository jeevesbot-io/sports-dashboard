<!--
Expected Goals League Table Component
-->
<template>
  <div class="xg-table">
    <!-- Controls -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-2">
        <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">xG League Table</h3>
        <Tag
          v-if="mockData"
          severity="warning"
          value="Simulated Data"
          icon="pi pi-info-circle"
        />
      </div>
      <Button
        @click="$emit('refresh')"
        :loading="loading"
        icon="pi pi-refresh"
        severity="secondary"
        size="small"
        text
      />
    </div>

    <!-- Table -->
    <DataTable
      :value="tableData"
      :loading="loading"
      responsive-layout="scroll"
      class="p-datatable-sm"
      :rows="20"
      :paginator="tableData.length > 20"
      sort-field="xg_diff"
      :sort-order="-1"
    >
      <Column field="position" header="Pos" style="width: 60px">
        <template #body="slotProps">
          <div class="font-bold text-center">{{ slotProps.index + 1 }}</div>
        </template>
      </Column>
      <Column field="team" header="Team" style="min-width: 180px">
        <template #body="slotProps">
          <div class="font-medium">{{ slotProps.data.team }}</div>
        </template>
      </Column>
      <Column field="matches" header="MP" sortable style="width: 70px" class="text-center" />
      <Column field="xg_for" header="xGF" sortable style="width: 80px">
        <template #body="slotProps">
          <div class="text-center font-mono">{{ slotProps.data.xg_for.toFixed(1) }}</div>
        </template>
      </Column>
      <Column field="xg_against" header="xGA" sortable style="width: 80px">
        <template #body="slotProps">
          <div class="text-center font-mono">{{ slotProps.data.xg_against.toFixed(1) }}</div>
        </template>
      </Column>
      <Column field="xg_diff" header="xGD" sortable style="width: 80px">
        <template #body="slotProps">
          <div
            class="text-center font-mono font-bold"
            :class="{
              'text-[var(--sd-win)]': slotProps.data.xg_diff > 0,
              'text-[var(--sd-loss)]': slotProps.data.xg_diff < 0,
              'text-[var(--sd-text-muted)]': slotProps.data.xg_diff === 0
            }"
          >
            {{ slotProps.data.xg_diff > 0 ? '+' : '' }}{{ slotProps.data.xg_diff.toFixed(1) }}
          </div>
        </template>
      </Column>
      <Column field="goals_for" header="GF" sortable style="width: 70px" class="text-center" />
      <Column field="goals_against" header="GA" sortable style="width: 70px" class="text-center" />
      <Column field="goal_diff" header="GD" sortable style="width: 70px">
        <template #body="slotProps">
          <div
            class="text-center font-bold"
            :class="{
              'text-[var(--sd-win)]': slotProps.data.goal_diff > 0,
              'text-[var(--sd-loss)]': slotProps.data.goal_diff < 0,
              'text-[var(--sd-text-muted)]': slotProps.data.goal_diff === 0
            }"
          >
            {{ slotProps.data.goal_diff > 0 ? '+' : '' }}{{ slotProps.data.goal_diff }}
          </div>
        </template>
      </Column>
      <Column field="overperformance" header="O/U" sortable style="width: 90px">
        <template #body="slotProps">
          <Tag
            :value="formatOverperformance(slotProps.data.overperformance)"
            :severity="getOverperformanceSeverity(slotProps.data.overperformance)"
            class="text-xs"
          />
        </template>
      </Column>
      <Column header="Trend" style="width: 100px">
        <template #body="slotProps">
          <div class="flex items-center justify-center">
            <div class="w-16 h-2 rounded-full bg-[var(--sd-surface-200)] overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :style="{
                  width: getPerformancePercentage(slotProps.data.overperformance) + '%',
                  background: getPerformanceGradient(slotProps.data.overperformance)
                }"
              ></div>
            </div>
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Legend -->
    <div class="glass-card p-3 mt-4" style="border-radius: 10px">
      <h4 class="text-xs font-semibold text-[var(--sd-text-muted)] uppercase tracking-wider mb-2">Legend</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-1.5 text-xs text-[var(--sd-text-muted)]">
        <div><strong class="text-[var(--sd-text-secondary)]">xGF/xGA:</strong> Expected Goals For/Against</div>
        <div><strong class="text-[var(--sd-text-secondary)]">xGD:</strong> Expected Goal Difference</div>
        <div><strong class="text-[var(--sd-text-secondary)]">O/U:</strong> Over/Under-performance vs xG</div>
        <div><strong class="text-[var(--sd-text-secondary)]">Trend:</strong> Visual indicator of performance vs expected</div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && tableData.length === 0" class="text-center py-8 text-[var(--sd-text-muted)]">
      <i class="pi pi-chart-line text-4xl mb-3"></i>
      <p>No xG data available.</p>
      <p class="text-sm">Try updating the xG data from the main page.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

interface XGTableData {
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

interface Props {
  data: XGTableData[]
  loading?: boolean
  mockData?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  mockData: false
})

defineEmits<{
  refresh: []
}>()

const tableData = computed(() => {
  return [...props.data].sort((a, b) => b.xg_diff - a.xg_diff)
})

const formatOverperformance = (value: number): string => {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(1)}`
}

const getOverperformanceSeverity = (value: number): string => {
  if (Math.abs(value) < 1) return 'secondary'
  if (value > 2) return 'success'
  if (value > 0) return 'info'
  if (value < -2) return 'danger'
  return 'warning'
}

const getPerformancePercentage = (value: number): number => {
  const maxValue = 10
  return Math.min(100, Math.max(0, ((value + maxValue) / (2 * maxValue)) * 100))
}

const getPerformanceGradient = (value: number): string => {
  if (value > 2) return 'var(--sd-gradient-3)'
  if (value > 0) return 'var(--sd-gradient-1)'
  if (value < -2) return 'var(--sd-gradient-4)'
  return 'var(--sd-gradient-2)'
}
</script>
