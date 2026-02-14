<template>
  <div class="season-projections">
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <i class="pi pi-spin pi-spinner text-2xl text-accent-cyan mb-3"></i>
        <p class="text-sm text-[var(--sd-text-muted)]">Running Monte Carlo simulations...</p>
      </div>
    </div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <template v-else>
      <DataTable
        :value="projections"
        :rows="20"
        sortMode="single"
        removableSort
        responsiveLayout="scroll"
        :rowClass="rowClass"
      >
        <Column header="#" :style="{ width: '50px' }">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column field="team" header="Team" sortable :style="{ minWidth: '160px' }">
          <template #body="{ data }">
            <span :class="{ 'text-[var(--sd-accent-cyan)] font-bold': isNewcastle(data.team) }">
              {{ data.team }}
            </span>
          </template>
        </Column>
        <Column field="current_points" header="Current Pts" sortable :style="{ width: '90px' }"></Column>
        <Column field="projected_points_mean" header="Proj. Pts" sortable :style="{ width: '90px' }">
          <template #body="{ data }">
            <span class="font-semibold font-mono">{{ data.projected_points_mean }}</span>
          </template>
        </Column>
        <Column header="Range (90%)" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span class="text-sm text-[var(--sd-text-muted)] font-mono">
              {{ data.projected_points_5th }} - {{ data.projected_points_95th }}
            </span>
          </template>
        </Column>
        <Column field="title_probability" header="Title %" sortable :style="{ width: '80px' }">
          <template #body="{ data }">
            <div class="probability-bar">
              <div class="bar" :style="{ width: data.title_probability + '%', background: 'var(--sd-gradient-1)' }"></div>
              <span class="bar-label">{{ data.title_probability }}%</span>
            </div>
          </template>
        </Column>
        <Column field="top4_probability" header="Top 4 %" sortable :style="{ width: '90px' }">
          <template #body="{ data }">
            <div class="probability-bar">
              <div class="bar" :style="{ width: data.top4_probability + '%', background: 'var(--sd-gradient-3)' }"></div>
              <span class="bar-label">{{ data.top4_probability }}%</span>
            </div>
          </template>
        </Column>
        <Column field="relegation_probability" header="Rel. %" sortable :style="{ width: '80px' }">
          <template #body="{ data }">
            <div class="probability-bar">
              <div class="bar" :style="{ width: data.relegation_probability + '%', background: 'var(--sd-gradient-4)' }"></div>
              <span class="bar-label">{{ data.relegation_probability }}%</span>
            </div>
          </template>
        </Column>
      </DataTable>
      <p class="text-xs text-[var(--sd-text-muted)] mt-3 text-center">
        Based on {{ simulationCount }} Monte Carlo simulations using Poisson model
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import type { TeamProjection } from '@/types'

const loading = ref(false)
const error = ref('')
const projections = ref<TeamProjection[]>([])
const simulationCount = ref(1000)

const isNewcastle = (name: string) => name?.includes('Newcastle')

const rowClass = (data: any) =>
  isNewcastle(data.team) ? 'focus-team-row' : ''

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getSeasonProjections()
    const data = response.data
    if (data) {
      projections.value = data.teams || []
      simulationCount.value = data.simulations || 1000
    }
  } catch (e: any) {
    error.value = 'Failed to generate season projections'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.probability-bar {
  position: relative;
  height: 20px;
  background: var(--sd-surface-200);
  border-radius: 6px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.bar-label {
  position: absolute;
  top: 50%;
  left: 6px;
  transform: translateY(-50%);
  font-size: 0.65rem;
  color: #fff;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
</style>
