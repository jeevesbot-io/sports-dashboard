<!--
Expected Goals League Table Component
-->
<template>
  <div class="xg-table">
    <!-- Controls -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-lg font-semibold">xG League Table</h3>
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
      striped-rows
    >
      <!-- Position -->
      <Column field="position" header="Pos" style="width: 60px">
        <template #body="slotProps">
          <div class="font-bold text-center">
            {{ slotProps.index + 1 }}
          </div>
        </template>
      </Column>

      <!-- Team -->
      <Column field="team" header="Team" style="min-width: 180px">
        <template #body="slotProps">
          <div class="font-medium">
            {{ slotProps.data.team }}
          </div>
        </template>
      </Column>

      <!-- Matches -->
      <Column 
        field="matches" 
        header="MP" 
        sortable 
        style="width: 70px"
        class="text-center"
      />

      <!-- xG For -->
      <Column 
        field="xg_for" 
        header="xGF" 
        sortable 
        style="width: 80px"
      >
        <template #body="slotProps">
          <div class="text-center font-mono">
            {{ slotProps.data.xg_for.toFixed(1) }}
          </div>
        </template>
      </Column>

      <!-- xG Against -->
      <Column 
        field="xg_against" 
        header="xGA" 
        sortable 
        style="width: 80px"
      >
        <template #body="slotProps">
          <div class="text-center font-mono">
            {{ slotProps.data.xg_against.toFixed(1) }}
          </div>
        </template>
      </Column>

      <!-- xG Difference -->
      <Column 
        field="xg_diff" 
        header="xGD" 
        sortable 
        style="width: 80px"
      >
        <template #body="slotProps">
          <div 
            class="text-center font-mono font-bold"
            :class="{
              'text-green-600': slotProps.data.xg_diff > 0,
              'text-red-600': slotProps.data.xg_diff < 0,
              'text-gray-600': slotProps.data.xg_diff === 0
            }"
          >
            {{ slotProps.data.xg_diff > 0 ? '+' : '' }}{{ slotProps.data.xg_diff.toFixed(1) }}
          </div>
        </template>
      </Column>

      <!-- Actual Goals For -->
      <Column 
        field="goals_for" 
        header="GF" 
        sortable 
        style="width: 70px"
        class="text-center"
      />

      <!-- Actual Goals Against -->
      <Column 
        field="goals_against" 
        header="GA" 
        sortable 
        style="width: 70px"
        class="text-center"
      />

      <!-- Goal Difference -->
      <Column 
        field="goal_diff" 
        header="GD" 
        sortable 
        style="width: 70px"
      >
        <template #body="slotProps">
          <div 
            class="text-center font-bold"
            :class="{
              'text-green-600': slotProps.data.goal_diff > 0,
              'text-red-600': slotProps.data.goal_diff < 0,
              'text-gray-600': slotProps.data.goal_diff === 0
            }"
          >
            {{ slotProps.data.goal_diff > 0 ? '+' : '' }}{{ slotProps.data.goal_diff }}
          </div>
        </template>
      </Column>

      <!-- Over/Under Performance -->
      <Column 
        field="overperformance" 
        header="O/U" 
        sortable 
        style="width: 90px"
      >
        <template #body="slotProps">
          <Tag
            :value="formatOverperformance(slotProps.data.overperformance)"
            :severity="getOverperformanceSeverity(slotProps.data.overperformance)"
            class="text-xs"
          />
        </template>
      </Column>

      <!-- Performance Indicator -->
      <Column header="Trend" style="width: 100px">
        <template #body="slotProps">
          <div class="flex items-center justify-center">
            <ProgressBar
              :value="getPerformancePercentage(slotProps.data.overperformance)"
              :show-value="false"
              class="w-16 h-2"
              :pt="{
                value: {
                  class: getPerformanceColor(slotProps.data.overperformance)
                }
              }"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Legend -->
    <div class="mt-4 p-3 bg-gray-50 rounded-lg">
      <h4 class="text-sm font-medium mb-2">Legend:</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
        <div><strong>xGF/xGA:</strong> Expected Goals For/Against</div>
        <div><strong>xGD:</strong> Expected Goal Difference</div>
        <div><strong>O/U:</strong> Over/Under-performance vs xG</div>
        <div><strong>Trend:</strong> Visual indicator of performance vs expected</div>
      </div>
    </div>

    <!-- Empty State -->
    <div 
      v-if="!loading && tableData.length === 0"
      class="text-center py-8 text-gray-500"
    >
      <i class="pi pi-chart-line text-4xl mb-3"></i>
      <p>No xG data available.</p>
      <p class="text-sm">Try updating the xG data from the main page.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'

// Types
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

// Props
interface Props {
  data: XGTableData[]
  loading?: boolean
  mockData?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  mockData: false
})

// Emits
defineEmits<{
  refresh: []
}>()

// Computed properties
const tableData = computed(() => {
  return [...props.data].sort((a, b) => b.xg_diff - a.xg_diff)
})

// Methods
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
  // Normalize to 0-100 scale for progress bar
  const maxValue = 10 // Assume max overperformance of ±10
  return Math.min(100, Math.max(0, ((value + maxValue) / (2 * maxValue)) * 100))
}

const getPerformanceColor = (value: number): string => {
  if (value > 2) return 'bg-green-500'
  if (value > 0) return 'bg-blue-500'
  if (value < -2) return 'bg-red-500'
  return 'bg-orange-500'
}
</script>

<style scoped>
.xg-table :deep(.p-datatable-thead > tr > th) {
  @apply text-xs font-semibold;
}

.xg-table :deep(.p-datatable-tbody > tr > td) {
  @apply text-sm;
}

.xg-table :deep(.p-progressbar) {
  @apply rounded-full;
}
</style>