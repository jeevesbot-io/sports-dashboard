<template>
  <div class="form-rating-card">
    <div v-if="loading" class="text-center py-8 text-[var(--sd-text-muted)]">Loading adjusted form...</div>
    <div v-else-if="error" class="text-center py-8 text-[var(--sd-loss)]">{{ error }}</div>
    <template v-else-if="formData">
      <!-- Gauge display -->
      <div class="flex items-center gap-8 mb-6">
        <div class="text-center">
          <div class="text-xs uppercase tracking-wider text-[var(--sd-text-muted)] mb-1">Last 5</div>
          <div
            class="font-display text-3xl font-bold"
            :style="{ color: getRatingColor(formData.form_rating_5) }"
          >
            {{ (formData.form_rating_5 * 100).toFixed(0) }}
          </div>
        </div>
        <div class="text-center">
          <div class="text-xs uppercase tracking-wider text-[var(--sd-text-muted)] mb-1">Last 10</div>
          <div
            class="font-display text-3xl font-bold"
            :style="{ color: getRatingColor(formData.form_rating_10) }"
          >
            {{ (formData.form_rating_10 * 100).toFixed(0) }}
          </div>
        </div>
        <div class="flex-1">
          <div class="flex gap-1">
            <span
              v-for="(char, i) in formData.form_string.split('')"
              :key="i"
              :class="['form-dot', `form-dot-${char === 'W' ? 'win' : char === 'D' ? 'draw' : 'loss'}`]"
              style="width: 24px; height: 24px; font-size: 10px;"
            >{{ char }}</span>
          </div>
        </div>
      </div>

      <!-- Match breakdown -->
      <div class="space-y-2">
        <div class="text-xs uppercase tracking-wider text-[var(--sd-text-muted)] mb-2">Match Breakdown</div>
        <div
          v-for="(match, i) in formData.breakdown"
          :key="i"
          class="flex items-center gap-3 p-2 rounded-lg"
          :class="{
            'bg-emerald-500/10': match.result === 'W',
            'bg-amber-500/10': match.result === 'D',
            'bg-red-500/10': match.result === 'L'
          }"
        >
          <span
            :class="['form-dot', `form-dot-${match.result === 'W' ? 'win' : match.result === 'D' ? 'draw' : 'loss'}`]"
            style="width: 22px; height: 22px; font-size: 9px;"
          >{{ match.result }}</span>
          <span class="text-sm text-[var(--sd-text-primary)] flex-1">
            {{ match.is_home ? 'vs' : '@' }} {{ match.opponent.replace(' FC', '') }}
          </span>
          <span class="text-xs text-[var(--sd-text-muted)]">
            Rating: {{ (match.opponent_rating * 100).toFixed(0) }}
          </span>
          <span
            class="text-xs font-mono font-semibold"
            :class="{
              'text-emerald-400': match.contribution > 0,
              'text-red-400': match.contribution < 0,
              'text-amber-400': match.contribution === 0
            }"
          >
            {{ match.contribution > 0 ? '+' : '' }}{{ match.contribution.toFixed(3) }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import apiClient from '@/api'
import type { OpponentAdjustedForm } from '@/types'

const props = defineProps<{
  teamId: number
}>()

const loading = ref(false)
const error = ref('')
const formData = ref<OpponentAdjustedForm | null>(null)

const getRatingColor = (rating: number) => {
  if (rating >= 0.65) return '#10b981'
  if (rating >= 0.45) return '#f59e0b'
  return '#ef4444'
}

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getOpponentAdjustedForm(props.teamId)
    formData.value = response.data || null
  } catch (e: any) {
    error.value = 'Failed to load adjusted form data'
  } finally {
    loading.value = false
  }
}

watch(() => props.teamId, loadData)
onMounted(loadData)
</script>
