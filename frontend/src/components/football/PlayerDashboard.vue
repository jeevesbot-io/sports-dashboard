<template>
  <div class="player-dashboard">
    <!-- Controls -->
    <div class="flex flex-wrap gap-3 items-end mb-5">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">Search Player</label>
        <InputText
          v-model="searchQuery"
          placeholder="Search by name..."
          class="w-full"
          @input="debouncedLoad"
        />
      </div>
      <div class="min-w-[180px]">
        <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">Team Filter</label>
        <InputText
          v-model="teamFilter"
          placeholder="Filter by team..."
          class="w-full"
          @input="debouncedLoad"
        />
      </div>
      <div class="flex gap-1">
        <button
          v-for="opt in sourceOptions"
          :key="opt.value"
          @click="dataSource = opt.value; loadData()"
          :class="[
            'pill-nav-item text-xs',
            dataSource === opt.value ? 'pill-nav-item-active' : ''
          ]"
        >
          {{ opt.label }}
        </button>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Refresh"
        severity="secondary"
        size="small"
        :loading="loading"
        @click="loadData"
      />
    </div>

    <!-- Understat Player Table -->
    <div v-if="dataSource === 'understat'">
      <DataTable
        :value="players"
        :loading="loading"
        :rows="20"
        :paginator="players.length > 20"
        sortMode="single"
        removableSort
        responsiveLayout="scroll"
        :rowClass="playerRowClass"
      >
        <Column field="name" header="Player" sortable :style="{ minWidth: '150px' }">
          <template #body="{ data }">
            <span class="font-medium">{{ data.name }}</span>
          </template>
        </Column>
        <Column field="team_name" header="Team" sortable :style="{ width: '130px' }">
          <template #body="{ data }">
            <span :class="{ 'text-[var(--sd-accent-cyan)] font-semibold': isNewcastle(data.team_name) }">
              {{ data.team_name }}
            </span>
          </template>
        </Column>
        <Column field="games" header="GP" sortable :style="{ width: '60px' }"></Column>
        <Column field="goals" header="G" sortable :style="{ width: '60px' }"></Column>
        <Column field="xg" header="xG" sortable :style="{ width: '70px' }">
          <template #body="{ data }">
            <span class="font-mono">{{ data.xg?.toFixed(1) }}</span>
          </template>
        </Column>
        <Column field="assists" header="A" sortable :style="{ width: '60px' }"></Column>
        <Column field="xa" header="xA" sortable :style="{ width: '70px' }">
          <template #body="{ data }">
            <span class="font-mono">{{ data.xa?.toFixed(1) }}</span>
          </template>
        </Column>
        <Column field="shots" header="Sh" sortable :style="{ width: '60px' }"></Column>
        <Column field="minutes" header="Min" sortable :style="{ width: '70px' }"></Column>
        <Column field="xg_per_90" header="xG/90" sortable :style="{ width: '80px' }">
          <template #body="{ data }">
            <span class="font-mono">{{ data.xg_per_90?.toFixed(2) }}</span>
          </template>
        </Column>
        <Column field="goals_minus_xg" header="G-xG" sortable :style="{ width: '80px' }">
          <template #body="{ data }">
            <span :class="{
              'text-[var(--sd-win)]': data.goals_minus_xg > 0,
              'text-[var(--sd-loss)]': data.goals_minus_xg < 0
            }" class="font-mono font-semibold">
              {{ data.goals_minus_xg > 0 ? '+' : '' }}{{ data.goals_minus_xg?.toFixed(1) }}
            </span>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- FBref Advanced Player Table -->
    <div v-else>
      <DataTable
        :value="advancedPlayers"
        :loading="loading"
        :rows="20"
        :paginator="advancedPlayers.length > 20"
        sortMode="single"
        removableSort
        responsiveLayout="scroll"
      >
        <Column field="player_name" header="Player" sortable :style="{ minWidth: '150px' }"></Column>
        <Column field="team_name" header="Team" sortable :style="{ width: '130px' }"></Column>
        <Column field="position" header="Pos" sortable :style="{ width: '60px' }"></Column>
        <Column field="minutes_90s" header="90s" sortable :style="{ width: '60px' }">
          <template #body="{ data }"><span class="font-mono">{{ data.minutes_90s?.toFixed(1) }}</span></template>
        </Column>
        <Column field="progressive_passes" header="PrgP" sortable :style="{ width: '70px' }"></Column>
        <Column field="progressive_carries" header="PrgC" sortable :style="{ width: '70px' }"></Column>
        <Column field="sca" header="SCA" sortable :style="{ width: '60px' }"></Column>
        <Column field="gca" header="GCA" sortable :style="{ width: '60px' }"></Column>
        <Column field="pressures" header="Press" sortable :style="{ width: '70px' }"></Column>
        <Column field="tackles" header="Tkl" sortable :style="{ width: '60px' }"></Column>
        <Column field="interceptions" header="Int" sortable :style="{ width: '60px' }"></Column>
        <Column field="pass_completion_pct" header="Pass%" sortable :style="{ width: '70px' }">
          <template #body="{ data }"><span class="font-mono">{{ data.pass_completion_pct?.toFixed(1) }}%</span></template>
        </Column>
      </DataTable>
    </div>

    <div v-if="!loading && players.length === 0 && dataSource === 'understat'" class="text-center py-8 text-[var(--sd-text-muted)]">
      <p>No player data available. Click "Update Player Data" in the header to ingest data.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import type { PlayerStats, AdvancedPlayerStats } from '@/types'

const loading = ref(false)
const searchQuery = ref('')
const teamFilter = ref('')
const dataSource = ref('understat')
const players = ref<PlayerStats[]>([])
const advancedPlayers = ref<AdvancedPlayerStats[]>([])

const sourceOptions = [
  { label: 'xG Stats', value: 'understat' },
  { label: 'Advanced', value: 'fbref' }
]

let debounceTimer: ReturnType<typeof setTimeout>

const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadData, 400)
}

const loadData = async () => {
  loading.value = true
  try {
    if (dataSource.value === 'understat') {
      const response = await apiClient.getPlayers({
        search: searchQuery.value || undefined,
        team: teamFilter.value || undefined,
        limit: 100
      })
      players.value = response.data || []
    } else {
      const response = await apiClient.getAdvancedPlayerStats({
        search: searchQuery.value || undefined,
        team: teamFilter.value || undefined,
        limit: 100
      })
      advancedPlayers.value = response.data || []
    }
  } catch (e) {
    console.error('Error loading player data:', e)
  } finally {
    loading.value = false
  }
}

const isNewcastle = (teamName: string) =>
  teamName?.includes('Newcastle')

const playerRowClass = (data: any) =>
  isNewcastle(data.team_name) ? 'focus-team-row' : ''

onMounted(loadData)
</script>
