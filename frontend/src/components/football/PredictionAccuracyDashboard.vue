<template>
  <div class="prediction-accuracy-dashboard">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading prediction data...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <template v-else>
      <!-- Accuracy Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat-card-glass relative overflow-hidden" style="background: var(--sd-gradient-1)">
          <div class="relative z-10">
            <div class="text-white/70 text-xs font-semibold uppercase tracking-wider mb-2">Total Predictions</div>
            <div class="font-display text-2xl font-bold text-white">{{ accuracy?.total || 0 }}</div>
          </div>
        </div>
        <div class="stat-card-glass relative overflow-hidden" style="background: var(--sd-gradient-2)">
          <div class="relative z-10">
            <div class="text-white/70 text-xs font-semibold uppercase tracking-wider mb-2">Outcome Accuracy</div>
            <div class="font-display text-2xl font-bold text-white">{{ accuracy?.outcome_accuracy?.toFixed(1) || 0 }}%</div>
          </div>
        </div>
        <div class="stat-card-glass relative overflow-hidden" style="background: var(--sd-gradient-3)">
          <div class="relative z-10">
            <div class="text-white/70 text-xs font-semibold uppercase tracking-wider mb-2">Score Accuracy</div>
            <div class="font-display text-2xl font-bold text-white">{{ accuracy?.score_accuracy?.toFixed(1) || 0 }}%</div>
          </div>
        </div>
        <div class="stat-card-glass relative overflow-hidden" style="background: var(--sd-gradient-4)">
          <div class="relative z-10">
            <div class="text-white/70 text-xs font-semibold uppercase tracking-wider mb-2">Avg Error</div>
            <div class="font-display text-2xl font-bold text-white">{{ accuracy?.avg_error?.toFixed(2) || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex gap-2 mb-6">
        <button
          @click="updateResults"
          :disabled="updating"
          class="pill-nav-item flex items-center gap-2 text-sm"
        >
          <i class="pi pi-sync" :class="{ 'animate-spin': updating }"></i>
          Update Results
        </button>
      </div>

      <!-- Recent predictions table -->
      <div v-if="history.length" class="space-y-2">
        <div class="text-xs uppercase tracking-wider text-[var(--sd-text-muted)] mb-2">Recent Predictions</div>
        <div
          v-for="record in history"
          :key="record.id"
          class="flex items-center gap-3 p-3 rounded-xl border transition-colors"
          :class="{
            'border-emerald-500/20 bg-emerald-500/5': record.outcome_correct === true,
            'border-red-500/20 bg-red-500/5': record.outcome_correct === false,
            'border-white/5 bg-white/5': record.outcome_correct === null || record.outcome_correct === undefined
          }"
        >
          <div class="flex-1">
            <div class="text-sm text-[var(--sd-text-primary)]">
              Fixture #{{ record.fixture_id }}
            </div>
            <div class="text-xs text-[var(--sd-text-muted)]">
              Predicted: {{ record.predicted_home_score.toFixed(1) }} - {{ record.predicted_away_score.toFixed(1) }}
              | Probs: {{ (record.home_win_prob * 100).toFixed(0) }}% / {{ (record.draw_prob * 100).toFixed(0) }}% / {{ (record.away_win_prob * 100).toFixed(0) }}%
            </div>
          </div>
          <div v-if="record.actual_home_score !== null && record.actual_home_score !== undefined" class="text-right">
            <div class="text-sm font-mono font-semibold text-[var(--sd-text-primary)]">
              {{ record.actual_home_score }} - {{ record.actual_away_score }}
            </div>
            <div class="text-xs">
              <span v-if="record.outcome_correct" class="text-emerald-400">Correct</span>
              <span v-else class="text-red-400">Wrong</span>
              <span v-if="record.score_correct" class="text-emerald-400 ml-1">(Exact!)</span>
            </div>
          </div>
          <div v-else class="text-xs text-[var(--sd-text-muted)]">Pending</div>
        </div>
      </div>
      <div v-else class="text-center py-4 text-[var(--sd-text-muted)]">
        No predictions stored yet. Use the Match Predictor to generate and save predictions.
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import apiClient from '@/api'
import type { PredictionAccuracy, PredictionRecord } from '@/types'

const toast = useToast()
const loading = ref(false)
const updating = ref(false)
const error = ref('')
const accuracy = ref<PredictionAccuracy | null>(null)
const history = ref<PredictionRecord[]>([])

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const [accResp, histResp] = await Promise.all([
      apiClient.getPredictionAccuracy(),
      apiClient.getPredictionHistory()
    ])
    accuracy.value = accResp.data || null
    history.value = histResp.data || []
  } catch (e: any) {
    error.value = 'Failed to load prediction data'
  } finally {
    loading.value = false
  }
}

const updateResults = async () => {
  updating.value = true
  try {
    const response = await apiClient.updatePredictionResults()
    toast.add({
      severity: 'success',
      summary: 'Results Updated',
      detail: `Updated ${(response.data as any)?.updated || 0} predictions`,
      life: 3000
    })
    await loadData()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Failed', detail: 'Could not update results', life: 3000 })
  } finally {
    updating.value = false
  }
}

onMounted(loadData)
</script>
