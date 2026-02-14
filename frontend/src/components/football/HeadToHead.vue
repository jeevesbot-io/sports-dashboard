<!--
Head-to-Head Analysis Component
-->
<template>
  <div class="head-to-head max-w-5xl mx-auto">
    <div class="glass-card p-6">
      <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)] mb-5">Head-to-Head Analysis</h3>

      <!-- Team Selection -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">First Team</label>
          <Dropdown
            v-model="selectedTeam1"
            :options="teams"
            option-label="name"
            option-value="name"
            placeholder="Select first team"
            filter
            class="w-full"
            :loading="loadingTeams"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">Second Team</label>
          <Dropdown
            v-model="selectedTeam2"
            :options="teams"
            option-label="name"
            option-value="name"
            placeholder="Select second team"
            filter
            class="w-full"
            :loading="loadingTeams"
          />
        </div>
      </div>

      <!-- Search Button -->
      <div class="mb-6">
        <Button
          @click="loadHeadToHead"
          :disabled="!canSearch"
          :loading="loading"
          label="Analyze Head-to-Head"
          icon="pi pi-search"
          class="w-full md:w-auto"
        />
      </div>

      <!-- Results -->
      <div v-if="h2hData" class="space-y-5">
        <!-- Record Summary -->
        <div class="grid grid-cols-3 gap-4">
          <div class="glass-card p-4 text-center" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-win)] mb-2">{{ h2hData.team1.name }} Wins</div>
            <div class="font-display text-3xl font-bold text-[var(--sd-text-primary)]">{{ h2hData.team1_wins }}</div>
          </div>
          <div class="glass-card p-4 text-center" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-2">Draws</div>
            <div class="font-display text-3xl font-bold text-[var(--sd-text-primary)]">{{ h2hData.draws }}</div>
          </div>
          <div class="glass-card p-4 text-center" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-accent-cyan)] mb-2">{{ h2hData.team2.name }} Wins</div>
            <div class="font-display text-3xl font-bold text-[var(--sd-text-primary)]">{{ h2hData.team2_wins }}</div>
          </div>
        </div>

        <!-- Win Percentage Bar -->
        <div class="glass-card p-5" style="border-radius: 12px">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Win Distribution</div>
          <div class="relative h-8 rounded-lg overflow-hidden bg-[var(--sd-surface-200)]">
            <div class="absolute left-0 top-0 h-full" :style="{ width: `${team1WinPercentage}%`, background: 'var(--sd-win)' }"></div>
            <div class="absolute top-0 h-full bg-[var(--sd-surface-400)]" :style="{ left: `${team1WinPercentage}%`, width: `${drawPercentage}%` }"></div>
            <div class="absolute right-0 top-0 h-full" :style="{ width: `${team2WinPercentage}%`, background: 'var(--sd-accent-cyan)' }"></div>
          </div>
          <div class="flex justify-between mt-2 text-xs text-[var(--sd-text-muted)]">
            <span>{{ team1WinPercentage.toFixed(1) }}%</span>
            <span>{{ drawPercentage.toFixed(1) }}% Draws</span>
            <span>{{ team2WinPercentage.toFixed(1) }}%</span>
          </div>
        </div>

        <!-- Goals Summary -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="glass-card p-5" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Goals Scored</div>
            <div class="flex justify-between items-center">
              <div class="text-center">
                <div class="font-display text-2xl font-bold text-[var(--sd-win)]">{{ h2hData.team1_goals }}</div>
                <div class="text-xs text-[var(--sd-text-muted)]">{{ h2hData.team1.name }}</div>
              </div>
              <div class="text-[var(--sd-text-muted)] text-sm">vs</div>
              <div class="text-center">
                <div class="font-display text-2xl font-bold text-[var(--sd-accent-cyan)]">{{ h2hData.team2_goals }}</div>
                <div class="text-xs text-[var(--sd-text-muted)]">{{ h2hData.team2.name }}</div>
              </div>
            </div>
          </div>
          <div class="glass-card p-5" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Avg Goals per Game</div>
            <div class="text-center">
              <div class="font-display text-2xl font-bold text-[var(--sd-text-primary)]">{{ averageGoalsPerGame.toFixed(2) }}</div>
              <div class="text-xs text-[var(--sd-text-muted)]">Total goals per match</div>
            </div>
          </div>
        </div>

        <!-- Match History -->
        <div class="glass-card p-5" style="border-radius: 12px">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">
            Recent Matches ({{ h2hData.total_matches }} total)
          </div>
          <DataTable
            :value="h2hData.matches"
            :rows="10"
            :paginator="h2hData.matches.length > 10"
            responsive-layout="scroll"
            class="p-datatable-sm"
          >
            <Column field="utc_date" header="Date">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.utc_date) }}
              </template>
            </Column>
            <Column header="Match">
              <template #body="slotProps">
                <div class="flex justify-between items-center">
                  <span>{{ slotProps.data.home_team.name }}</span>
                  <div class="mx-4 font-bold font-mono">
                    {{ slotProps.data.home_score }} - {{ slotProps.data.away_score }}
                  </div>
                  <span>{{ slotProps.data.away_team.name }}</span>
                </div>
              </template>
            </Column>
            <Column field="winner" header="Result">
              <template #body="slotProps">
                <Tag
                  :value="getResultText(slotProps.data)"
                  :severity="getResultSeverity(slotProps.data)"
                />
              </template>
            </Column>
          </DataTable>
        </div>
      </div>

      <!-- No Data Message -->
      <div v-else-if="!loading && searchAttempted" class="text-center py-8 text-[var(--sd-text-muted)]">
        <i class="pi pi-info-circle text-4xl mb-3"></i>
        <p>No matches found between these teams.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'

import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

import apiClient from '@/api'
import type { FootballTeam, HeadToHeadData } from '@/types'

const toast = useToast()
const teams = ref<FootballTeam[]>([])
const selectedTeam1 = ref<string>('')
const selectedTeam2 = ref<string>('')
const h2hData = ref<HeadToHeadData | null>(null)
const loading = ref(false)
const loadingTeams = ref(false)
const searchAttempted = ref(false)

const canSearch = computed(() => {
  return selectedTeam1.value && selectedTeam2.value &&
         selectedTeam1.value !== selectedTeam2.value
})

const team1WinPercentage = computed(() => {
  if (!h2hData.value || h2hData.value.total_matches === 0) return 0
  return (h2hData.value.team1_wins / h2hData.value.total_matches) * 100
})

const team2WinPercentage = computed(() => {
  if (!h2hData.value || h2hData.value.total_matches === 0) return 0
  return (h2hData.value.team2_wins / h2hData.value.total_matches) * 100
})

const drawPercentage = computed(() => {
  if (!h2hData.value || h2hData.value.total_matches === 0) return 0
  return (h2hData.value.draws / h2hData.value.total_matches) * 100
})

const averageGoalsPerGame = computed(() => {
  if (!h2hData.value || h2hData.value.total_matches === 0) return 0
  return (h2hData.value.team1_goals + h2hData.value.team2_goals) / h2hData.value.total_matches
})

const loadTeams = async () => {
  loadingTeams.value = true
  try {
    teams.value = await apiClient.getFootballTeams()
  } catch (error) {
    console.error('Error loading teams:', error)
    toast.add({ severity: 'error', summary: 'Load Error', detail: 'Failed to load teams', life: 3000 })
  } finally {
    loadingTeams.value = false
  }
}

const loadHeadToHead = async () => {
  if (!canSearch.value) return
  loading.value = true
  searchAttempted.value = true
  h2hData.value = null
  try {
    const response = await apiClient.getHeadToHead(selectedTeam1.value, selectedTeam2.value)
    h2hData.value = response.data || null
  } catch (error) {
    console.error('Error loading head-to-head:', error)
    toast.add({ severity: 'error', summary: 'Load Error', detail: 'Failed to load head-to-head data', life: 3000 })
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const getResultText = (match: any) => {
  if (!h2hData.value) return 'Unknown'
  const isTeam1Home = match.home_team.name === h2hData.value.team1.name
  const homeScore = match.home_score
  const awayScore = match.away_score
  if (homeScore === awayScore) return 'Draw'
  else if (homeScore > awayScore) return isTeam1Home ? h2hData.value.team1.name : h2hData.value.team2.name
  else return isTeam1Home ? h2hData.value.team2.name : h2hData.value.team1.name
}

const getResultSeverity = (match: any) => {
  if (!h2hData.value) return 'secondary'
  const resultText = getResultText(match)
  if (resultText === 'Draw') return 'secondary'
  if (resultText === h2hData.value.team1.name) return 'success'
  if (resultText === h2hData.value.team2.name) return 'info'
  return 'secondary'
}

onMounted(() => { loadTeams() })
</script>
