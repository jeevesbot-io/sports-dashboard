<!--
Match Prediction Component
-->
<template>
  <div class="match-predictor">
    <Card>
      <template #title>
        <div class="flex items-center gap-2">
          <i class="pi pi-calculator"></i>
          Match Predictor
        </div>
      </template>
      <template #content>
        <!-- Team Selection -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium mb-2">Home Team</label>
            <Dropdown
              v-model="homeTeam"
              :options="teams"
              option-label="name"
              option-value="name"
              placeholder="Select home team"
              filter
              class="w-full"
              :loading="loadingTeams"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Away Team</label>
            <Dropdown
              v-model="awayTeam"
              :options="teams"
              option-label="name"
              option-value="name"
              placeholder="Select away team"
              filter
              class="w-full"
              :loading="loadingTeams"
            />
          </div>
        </div>

        <!-- Predict Button -->
        <div class="mb-6 text-center">
          <Button
            @click="predictMatch"
            :disabled="!canPredict"
            :loading="loading"
            label="Predict Match Outcome"
            icon="pi pi-chart-line"
            size="large"
            class="w-full md:w-auto"
          />
        </div>

        <!-- Prediction Results -->
        <div v-if="prediction" class="space-y-6">
          <!-- Match Header -->
          <div class="text-center">
            <h3 class="text-xl font-bold mb-2">
              {{ prediction.home_team.name }} vs {{ prediction.away_team.name }}
            </h3>
            <div class="flex justify-center gap-4 text-sm text-gray-600">
              <span>Model: {{ prediction.model }}</span>
              <span>Confidence: {{ prediction.predictions.confidence }}%</span>
            </div>
          </div>

          <!-- Expected Goals -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card class="text-center">
              <template #title>{{ prediction.home_team.name }}</template>
              <template #content>
                <div class="space-y-2">
                  <div class="text-3xl font-bold text-blue-600">
                    {{ prediction.predictions.home_xg }}
                  </div>
                  <div class="text-sm text-gray-600">Expected Goals</div>
                  <div class="text-xs space-y-1">
                    <div>Attack: {{ prediction.home_team.attack_strength }}</div>
                    <div>Defense: {{ prediction.home_team.defense_strength }}</div>
                  </div>
                </div>
              </template>
            </Card>
            
            <Card class="text-center">
              <template #title>{{ prediction.away_team.name }}</template>
              <template #content>
                <div class="space-y-2">
                  <div class="text-3xl font-bold text-green-600">
                    {{ prediction.predictions.away_xg }}
                  </div>
                  <div class="text-sm text-gray-600">Expected Goals</div>
                  <div class="text-xs space-y-1">
                    <div>Attack: {{ prediction.away_team.attack_strength }}</div>
                    <div>Defense: {{ prediction.away_team.defense_strength }}</div>
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- Probabilities -->
          <Card>
            <template #title>Match Outcome Probabilities</template>
            <template #content>
              <div class="space-y-4">
                <!-- Home Win -->
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="font-medium">{{ prediction.home_team.name }} Win</span>
                    <span class="font-bold text-blue-600">
                      {{ prediction.predictions.home_win_prob }}%
                    </span>
                  </div>
                  <ProgressBar
                    :value="prediction.predictions.home_win_prob"
                    :show-value="false"
                    class="h-3"
                    :pt="{
                      value: { class: 'bg-blue-500' }
                    }"
                  />
                </div>

                <!-- Draw -->
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="font-medium">Draw</span>
                    <span class="font-bold text-gray-600">
                      {{ prediction.predictions.draw_prob }}%
                    </span>
                  </div>
                  <ProgressBar
                    :value="prediction.predictions.draw_prob"
                    :show-value="false"
                    class="h-3"
                    :pt="{
                      value: { class: 'bg-gray-500' }
                    }"
                  />
                </div>

                <!-- Away Win -->
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="font-medium">{{ prediction.away_team.name }} Win</span>
                    <span class="font-bold text-green-600">
                      {{ prediction.predictions.away_win_prob }}%
                    </span>
                  </div>
                  <ProgressBar
                    :value="prediction.predictions.away_win_prob"
                    :show-value="false"
                    class="h-3"
                    :pt="{
                      value: { class: 'bg-green-500' }
                    }"
                  />
                </div>
              </div>
            </template>
          </Card>

          <!-- Most Likely Score -->
          <Card>
            <template #title>Most Likely Score</template>
            <template #content>
              <div class="text-center">
                <div class="text-4xl font-bold mb-2">
                  {{ prediction.predictions.most_likely_score }}
                </div>
                <div class="text-sm text-gray-600">
                  Based on Poisson distribution analysis
                </div>
              </div>
            </template>
          </Card>

          <!-- Model Info -->
          <div class="p-4 bg-gray-50 rounded-lg text-sm">
            <h4 class="font-medium mb-2">About This Prediction</h4>
            <ul class="space-y-1 text-gray-600">
              <li>• Based on recent form and historical performance</li>
              <li>• Uses Poisson distribution for goal probability</li>
              <li>• Includes home advantage factor (1.25x)</li>
              <li>• Analyzes last 20 matches for team strength</li>
            </ul>
          </div>
        </div>

        <!-- No Data Message -->
        <div
          v-else-if="!loading && predictionAttempted"
          class="text-center py-8 text-gray-500"
        >
          <i class="pi pi-exclamation-triangle text-4xl mb-3"></i>
          <p>Unable to generate prediction for these teams.</p>
          <p class="text-sm">Make sure both teams exist and have recent match data.</p>
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
import ProgressBar from 'primevue/progressbar'

// Services
import apiClient from '@/api'
import type { FootballTeam, MatchPrediction } from '@/types'

// Reactive state
const toast = useToast()
const teams = ref<FootballTeam[]>([])
const homeTeam = ref<string>('')
const awayTeam = ref<string>('')
const prediction = ref<MatchPrediction | null>(null)
const loading = ref(false)
const loadingTeams = ref(false)
const predictionAttempted = ref(false)

// Computed properties
const canPredict = computed(() => {
  return homeTeam.value && awayTeam.value && 
         homeTeam.value !== awayTeam.value
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

const predictMatch = async () => {
  if (!canPredict.value) return

  loading.value = true
  predictionAttempted.value = true
  prediction.value = null

  try {
    const response = await apiClient.predictMatch(homeTeam.value, awayTeam.value)
    prediction.value = response.data || null

    toast.add({
      severity: 'success',
      summary: 'Prediction Generated',
      detail: `Confidence: ${prediction.value?.predictions.confidence}%`,
      life: 3000
    })
  } catch (error) {
    console.error('Error predicting match:', error)
    toast.add({
      severity: 'error',
      summary: 'Prediction Failed',
      detail: 'Failed to generate match prediction',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadTeams()
})
</script>

<style scoped>
.match-predictor {
  @apply max-w-4xl mx-auto;
}

:deep(.p-progressbar) {
  @apply rounded-lg;
}

:deep(.p-progressbar .p-progressbar-value) {
  @apply transition-all duration-500 ease-out;
}
</style>