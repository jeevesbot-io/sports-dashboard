<template>
  <div class="advanced-stats-table">
    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="pi pi-spin pi-spinner text-2xl text-accent-cyan"></i>
    </div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <template v-else>
      <DataTable
        :value="stats"
        :rows="20"
        sortMode="single"
        removableSort
        responsiveLayout="scroll"
        :rowClass="rowClass"
      >
        <Column field="team_name" header="Team" sortable :style="{ minWidth: '160px' }">
          <template #body="{ data }">
            <span :class="{ 'text-[var(--sd-accent-cyan)] font-bold': isNewcastle(data.team_name) }">
              {{ data.team_name }}
            </span>
          </template>
        </Column>
        <Column field="possession_pct" header="Poss%" sortable :style="{ width: '75px' }">
          <template #body="{ data }">
            <span class="font-mono text-sm">{{ data.possession_pct?.toFixed(1) }}%</span>
          </template>
        </Column>
        <Column field="progressive_passes" header="PrgP" sortable :style="{ width: '70px' }"></Column>
        <Column field="progressive_carries" header="PrgC" sortable :style="{ width: '70px' }"></Column>
        <Column field="pressures" header="Press" sortable :style="{ width: '70px' }"></Column>
        <Column field="pressure_success_pct" header="Press%" sortable :style="{ width: '75px' }">
          <template #body="{ data }">
            <span class="font-mono text-sm">{{ data.pressure_success_pct?.toFixed(1) }}%</span>
          </template>
        </Column>
        <Column field="tackles" header="Tkl" sortable :style="{ width: '60px' }"></Column>
        <Column field="interceptions" header="Int" sortable :style="{ width: '60px' }"></Column>
        <Column field="blocks" header="Blk" sortable :style="{ width: '60px' }"></Column>
        <Column field="sca" header="SCA" sortable :style="{ width: '60px' }"></Column>
        <Column field="gca" header="GCA" sortable :style="{ width: '60px' }"></Column>
        <Column field="pass_completion_pct" header="Pass%" sortable :style="{ width: '75px' }">
          <template #body="{ data }">
            <span class="font-mono text-sm">{{ data.pass_completion_pct?.toFixed(1) }}%</span>
          </template>
        </Column>
      </DataTable>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import type { AdvancedTeamStats } from '@/types'

const loading = ref(false)
const error = ref('')
const stats = ref<AdvancedTeamStats[]>([])

const isNewcastle = (name: string) => name?.includes('Newcastle')
const rowClass = (data: any) => isNewcastle(data.team_name) ? 'focus-team-row' : ''

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getAdvancedTeamStats()
    stats.value = response.data || []
  } catch (e: any) {
    error.value = 'Failed to load advanced stats'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
