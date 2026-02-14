<!--
Match Prediction Component
-->
<template>
  <div class="match-predictor max-w-4xl mx-auto">
    <div class="glass-card p-6">
      <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)] mb-5 flex items-center gap-2">
        <i class="pi pi-calculator text-accent-cyan"></i>
        Match Predictor
      </h3>

      <!-- Team Selection -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">Home Team</label>
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
          <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1.5">Away Team</label>
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
      <div v-if="prediction" class="space-y-5">
        <!-- Match Header -->
        <div class="text-center">
          <h3 class="font-display text-xl font-bold text-[var(--sd-text-primary)] mb-2">
            {{ prediction.home_team.name }} vs {{ prediction.away_team.name }}
          </h3>
          <div class="flex justify-center gap-4 text-xs text-[var(--sd-text-muted)]">
            <span>Model: {{ prediction.model }}</span>
            <span>Confidence: {{ prediction.predictions.confidence }}%</span>
          </div>
        </div>

        <!-- Expected Goals -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="glass-card p-5 text-center" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-2">{{ prediction.home_team.name }}</div>
            <div class="font-display text-3xl font-bold text-[var(--sd-accent-cyan)] mb-1">{{ prediction.predictions.home_xg }}</div>
            <div class="text-xs text-[var(--sd-text-muted)] mb-3">Expected Goals</div>
            <div class="text-xs text-[var(--sd-text-muted)] space-y-0.5">
              <div>Attack: {{ prediction.home_team.attack_strength }}</div>
              <div>Defense: {{ prediction.home_team.defense_strength }}</div>
            </div>
          </div>
          <div class="glass-card p-5 text-center" style="border-radius: 12px">
            <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-2">{{ prediction.away_team.name }}</div>
            <div class="font-display text-3xl font-bold text-[var(--sd-accent-violet)] mb-1">{{ prediction.predictions.away_xg }}</div>
            <div class="text-xs text-[var(--sd-text-muted)] mb-3">Expected Goals</div>
            <div class="text-xs text-[var(--sd-text-muted)] space-y-0.5">
              <div>Attack: {{ prediction.away_team.attack_strength }}</div>
              <div>Defense: {{ prediction.away_team.defense_strength }}</div>
            </div>
          </div>
        </div>

        <!-- Probabilities -->
        <div class="glass-card p-5 space-y-4" style="border-radius: 12px">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-1">Match Outcome Probabilities</div>

          <div v-for="item in probItems" :key="item.label">
            <div class="flex justify-between items-center mb-1.5">
              <span class="text-sm font-medium text-[var(--sd-text-primary)]">{{ item.label }}</span>
              <span class="font-mono font-bold text-sm" :style="{ color: item.color }">{{ item.value }}%</span>
            </div>
            <div class="relative h-3 bg-[var(--sd-surface-200)] rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500" :style="{ width: item.value + '%', background: item.gradient }"></div>
            </div>
          </div>
        </div>

        <!-- Most Likely Score -->
        <div class="glass-card p-5 text-center" style="border-radius: 12px">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Most Likely Score</div>
          <div class="font-display text-4xl font-bold gradient-text mb-2">{{ prediction.predictions.most_likely_score }}</div>
          <div class="text-xs text-[var(--sd-text-muted)]">Based on Poisson distribution analysis</div>
        </div>

        <!-- Head-to-Head Summary -->
        <div v-if="h2hData" class="glass-card p-5" style="border-radius: 12px">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Head-to-Head Record</div>
          <div class="grid grid-cols-3 gap-4 text-center mb-4">
            <div>
              <span class="block font-display text-2xl font-bold text-[var(--sd-accent-cyan)]">{{ h2hData.team1_wins }}</span>
              <span class="text-xs text-[var(--sd-text-muted)]">{{ prediction.home_team.name }} Wins</span>
            </div>
            <div>
              <span class="block font-display text-2xl font-bold text-[var(--sd-draw)]">{{ h2hData.draws }}</span>
              <span class="text-xs text-[var(--sd-text-muted)]">Draws</span>
            </div>
            <div>
              <span class="block font-display text-2xl font-bold text-[var(--sd-accent-violet)]">{{ h2hData.team2_wins }}</span>
              <span class="text-xs text-[var(--sd-text-muted)]">{{ prediction.away_team.name }} Wins</span>
            </div>
          </div>
          <div v-if="h2hData.matches.length" class="space-y-2">
            <div class="text-xs font-semibold text-[var(--sd-text-muted)] mb-1">Last {{ Math.min(h2hData.matches.length, 5) }} Meetings</div>
            <div
              v-for="match in h2hData.matches.slice(0, 5)"
              :key="match.id"
              class="flex justify-between items-center p-2 rounded-lg bg-white/5 text-xs"
            >
              <span class="text-[var(--sd-text-secondary)]">{{ match.home_team?.short_name || 'Home' }} {{ match.home_score }} - {{ match.away_score }} {{ match.away_team?.short_name || 'Away' }}</span>
              <span class="text-[var(--sd-text-muted)]">{{ new Date(match.utc_date).toLocaleDateString() }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-[var(--sd-text-muted)] text-center">No previous meetings found</div>
        </div>

        <!-- Save Prediction Button -->
        <div class="text-center">
          <Button
            @click="savePrediction"
            :loading="saving"
            :disabled="predictionSaved"
            :label="predictionSaved ? 'Prediction Saved' : 'Save Prediction'"
            :icon="predictionSaved ? 'pi pi-check' : 'pi pi-save'"
            :severity="predictionSaved ? 'success' : undefined"
            size="small"
            class="w-full md:w-auto"
          />
        </div>

        <!-- Model Info -->
        <div class="glass-card p-4 text-sm" style="border-radius: 12px">
          <h4 class="font-semibold text-[var(--sd-text-primary)] mb-2 text-xs uppercase tracking-wider">About This Prediction</h4>
          <ul class="space-y-1 text-[var(--sd-text-muted)] text-xs">
            <li>Based on recent form and historical performance</li>
            <li>Uses Poisson distribution for goal probability</li>
            <li>Includes home advantage factor (1.25x)</li>
            <li>Analyzes last 20 matches for team strength</li>
          </ul>
        </div>
      </div>

      <!-- No Data Message -->
      <div v-else-if="!loading && predictionAttempted" class="text-center py-8 text-[var(--sd-text-muted)]">
        <i class="pi pi-exclamation-triangle text-4xl mb-3"></i>
        <p>Unable to generate prediction for these teams.</p>
        <p class="text-xs">Make sure both teams exist and have recent match data.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'

import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'

import apiClient from '@/api'
import type { FootballTeam, MatchPrediction, HeadToHeadData } from '@/types'

const toast = useToast()
const teams = ref<FootballTeam[]>([])
const homeTeam = ref<string>('')
const awayTeam = ref<string>('')
const prediction = ref<MatchPrediction | null>(null)
const h2hData = ref<HeadToHeadData | null>(null)
const loading = ref(false)
const loadingTeams = ref(false)
const predictionAttempted = ref(false)
const saving = ref(false)
const predictionSaved = ref(false)

const canPredict = computed(() => {
  return homeTeam.value && awayTeam.value && homeTeam.value !== awayTeam.value
})

const probItems = computed(() => {
  if (!prediction.value) return []
  return [
    {
      label: `${prediction.value.home_team.name} Win`,
      value: prediction.value.predictions.home_win_prob,
      color: 'var(--sd-accent-cyan)',
      gradient: 'var(--sd-gradient-3)'
    },
    {
      label: 'Draw',
      value: prediction.value.predictions.draw_prob,
      color: 'var(--sd-draw)',
      gradient: 'linear-gradient(135deg, #f59e0b, #f97316)'
    },
    {
      label: `${prediction.value.away_team.name} Win`,
      value: prediction.value.predictions.away_win_prob,
      color: 'var(--sd-accent-violet)',
      gradient: 'var(--sd-gradient-1)'
    }
  ]
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

const predictMatch = async () => {
  if (!canPredict.value) return
  loading.value = true
  predictionAttempted.value = true
  prediction.value = null
  h2hData.value = null
  predictionSaved.value = false
  try {
    const [predResponse, h2hResponse] = await Promise.allSettled([
      apiClient.predictMatch(homeTeam.value, awayTeam.value),
      apiClient.getHeadToHead(homeTeam.value, awayTeam.value)
    ])
    if (predResponse.status === 'fulfilled') {
      prediction.value = predResponse.value.data || null
      toast.add({
        severity: 'success',
        summary: 'Prediction Generated',
        detail: `Confidence: ${prediction.value?.predictions.confidence}%`,
        life: 3000
      })
    }
    if (h2hResponse.status === 'fulfilled') {
      h2hData.value = h2hResponse.value.data || null
    }
  } catch (error) {
    console.error('Error predicting match:', error)
    toast.add({ severity: 'error', summary: 'Prediction Failed', detail: 'Failed to generate match prediction', life: 3000 })
  } finally {
    loading.value = false
  }
}

const savePrediction = async () => {
  if (!prediction.value) return
  saving.value = true
  try {
    const score = prediction.value.predictions.most_likely_score.split('-').map(Number)
    await apiClient.storePrediction({
      fixture_id: 0,
      predicted_home_score: score[0] ?? 0,
      predicted_away_score: score[1] ?? 0,
      home_win_prob: prediction.value.predictions.home_win_prob,
      draw_prob: prediction.value.predictions.draw_prob,
      away_win_prob: prediction.value.predictions.away_win_prob,
      model_name: prediction.value.model
    })
    predictionSaved.value = true
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Prediction saved for tracking', life: 3000 })
  } catch (error) {
    console.error('Error saving prediction:', error)
    toast.add({ severity: 'error', summary: 'Save Failed', detail: 'Could not save prediction', life: 3000 })
  } finally {
    saving.value = false
  }
}

onMounted(() => { loadTeams() })
</script>
