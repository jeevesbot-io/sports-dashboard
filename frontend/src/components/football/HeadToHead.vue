<!--
Head-to-Head Analysis Component
-->
<template>
  <div class="head-to-head">
    <Card>
      <template #title>Head-to-Head Analysis</template>
      <template #content>
        <!-- Team Selection -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium mb-2">First Team</label>
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
            <label class="block text-sm font-medium mb-2">Second Team</label>
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
        <div v-if="h2hData" class="space-y-6">
          <!-- Record Summary -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card class="text-center">
              <template #title>
                <div class="text-lg font-semibold text-green-600">
                  {{ h2hData.team1.name }} Wins
                </div>
              </template>
              <template #content>
                <div class="text-3xl font-bold">{{ h2hData.team1_wins }}</div>
              </template>
            </Card>
            
            <Card class="text-center">
              <template #title>
                <div class="text-lg font-semibold text-gray-600">Draws</div>
              </template>
              <template #content>
                <div class="text-3xl font-bold">{{ h2hData.draws }}</div>
              </template>
            </Card>
            
            <Card class="text-center">
              <template #title>
                <div class="text-lg font-semibold text-blue-600">
                  {{ h2hData.team2.name }} Wins
                </div>
              </template>
              <template #content>
                <div class="text-3xl font-bold">{{ h2hData.team2_wins }}</div>
              </template>
            </Card>
          </div>

          <!-- Win Percentage Bar -->
          <Card>
            <template #title>Win Distribution</template>
            <template #content>
              <div class="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
                <div
                  class="absolute left-0 top-0 h-full bg-green-500"
                  :style="{ width: `${team1WinPercentage}%` }"
                ></div>
                <div
                  class="absolute top-0 h-full bg-gray-400"
                  :style="{
                    left: `${team1WinPercentage}%`,
                    width: `${drawPercentage}%`
                  }"
                ></div>
                <div
                  class="absolute right-0 top-0 h-full bg-blue-500"
                  :style="{ width: `${team2WinPercentage}%` }"
                ></div>
              </div>
              <div class="flex justify-between mt-2 text-sm">
                <span>{{ team1WinPercentage.toFixed(1) }}%</span>
                <span>{{ drawPercentage.toFixed(1) }}% Draws</span>
                <span>{{ team2WinPercentage.toFixed(1) }}%</span>
              </div>
            </template>
          </Card>

          <!-- Goals Summary -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <template #title>Goals Scored</template>
              <template #content>
                <div class="flex justify-between items-center">
                  <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">
                      {{ h2hData.team1_goals }}
                    </div>
                    <div class="text-sm text-gray-600">
                      {{ h2hData.team1.name }}
                    </div>
                  </div>
                  <div class="text-gray-400">vs</div>
                  <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">
                      {{ h2hData.team2_goals }}
                    </div>
                    <div class="text-sm text-gray-600">
                      {{ h2hData.team2.name }}
                    </div>
                  </div>
                </div>
              </template>
            </Card>
            
            <Card>
              <template #title>Average Goals per Game</template>
              <template #content>
                <div class="text-center">
                  <div class="text-2xl font-bold">
                    {{ averageGoalsPerGame.toFixed(2) }}
                  </div>
                  <div class="text-sm text-gray-600">
                    Total goals per match
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- Match History -->
          <Card>
            <template #title>
              Recent Matches ({{ h2hData.total_matches }} total)
            </template>
            <template #content>
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
                      <div class="mx-4 font-bold">
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
            </template>
          </Card>
        </div>

        <!-- No Data Message -->
        <div
          v-else-if="!loading && searchAttempted"
          class="text-center py-8 text-gray-500"
        >
          <i class="pi pi-info-circle text-4xl mb-3"></i>
          <p>No matches found between these teams.</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'

// PrimeVue Components
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dropdown from 'primevue/dropdown'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

// Services
import apiClient from '@/api'
import type { FootballTeam, HeadToHeadData } from '@/types'

// Reactive state
const toast = useToast()
const teams = ref<FootballTeam[]>([])
const selectedTeam1 = ref<string>('')
const selectedTeam2 = ref<string>('')
const h2hData = ref<HeadToHeadData | null>(null)
const loading = ref(false)
const loadingTeams = ref(false)
const searchAttempted = ref(false)

// Computed properties
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

// Methods
const loadTeams = async () => {
  loadingTeams.value = true
  try {
    teams.value = await apiClient.getFootballTeams()
  } catch (error) {
    console.error('Error loading teams:', error)
    toast.add({
      severity: 'error',
      summary: 'Load Error',
      detail: 'Failed to load teams',
      life: 3000
    })
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
    toast.add({
      severity: 'error',
      summary: 'Load Error',
      detail: 'Failed to load head-to-head data',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getResultText = (match: any) => {
  if (!h2hData.value) return 'Unknown'
  
  const isTeam1Home = match.home_team.name === h2hData.value.team1.name
  const homeScore = match.home_score
  const awayScore = match.away_score
  
  if (homeScore === awayScore) {
    return 'Draw'
  } else if (homeScore > awayScore) {
    return isTeam1Home ? h2hData.value.team1.name : h2hData.value.team2.name
  } else {
    return isTeam1Home ? h2hData.value.team2.name : h2hData.value.team1.name
  }
}

const getResultSeverity = (match: any) => {
  if (!h2hData.value) return 'secondary'
  
  const resultText = getResultText(match)
  if (resultText === 'Draw') return 'secondary'
  if (resultText === h2hData.value.team1.name) return 'success'
  if (resultText === h2hData.value.team2.name) return 'info'
  return 'secondary'
}

// Lifecycle
onMounted(() => {
  loadTeams()
})
</script>

<style scoped>
.head-to-head {
  @apply max-w-6xl mx-auto;
}
</style>