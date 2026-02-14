<template>
  <div class="upcoming-matches-panel">
    <div v-if="loading" class="text-center py-6 text-[var(--sd-text-muted)]">Loading upcoming fixtures...</div>
    <div v-else-if="error" class="text-center py-6 text-[var(--sd-loss)]">{{ error }}</div>
    <template v-else-if="data && data.fixtures.length">
      <div class="flex items-center gap-3 mb-4">
        <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">
          Upcoming — Matchday {{ data.next_matchday }}
        </h3>
        <span class="text-xs text-[var(--sd-text-muted)]">{{ data.fixtures.length }} fixtures</span>
      </div>

      <div class="space-y-3">
        <div
          v-for="item in data.fixtures"
          :key="item.fixture.id"
          class="flex items-center gap-4 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
          @click="toggleExpand(item.fixture.id)"
        >
          <!-- Home team -->
          <div class="flex-1 text-right">
            <div class="flex items-center justify-end gap-2">
              <span class="text-sm font-medium text-[var(--sd-text-primary)]">
                {{ item.fixture.home_team.short_name }}
              </span>
              <img
                v-if="item.fixture.home_team.crest_url"
                :src="item.fixture.home_team.crest_url"
                class="w-5 h-5 object-contain"
                @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'"
              />
            </div>
          </div>

          <!-- Score / Time -->
          <div class="text-center min-w-[60px]">
            <div v-if="item.prediction" class="text-xs text-[var(--sd-text-muted)]">
              {{ item.prediction.home_xg?.toFixed(1) }} - {{ item.prediction.away_xg?.toFixed(1) }}
            </div>
            <div class="text-xs text-[var(--sd-text-muted)]">
              {{ formatDate(item.fixture.utc_date) }}
            </div>
          </div>

          <!-- Away team -->
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <img
                v-if="item.fixture.away_team.crest_url"
                :src="item.fixture.away_team.crest_url"
                class="w-5 h-5 object-contain"
                @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <span class="text-sm font-medium text-[var(--sd-text-primary)]">
                {{ item.fixture.away_team.short_name }}
              </span>
            </div>
          </div>

          <i class="pi pi-chevron-down text-xs text-[var(--sd-text-muted)] transition-transform"
             :class="{ 'rotate-180': expandedFixtures.has(item.fixture.id) }"
          ></i>
        </div>

        <!-- Expanded prediction -->
        <div
          v-for="item in data.fixtures.filter(f => expandedFixtures.has(f.fixture.id) && f.prediction)"
          :key="'detail-' + item.fixture.id"
          class="p-3 rounded-xl bg-white/5 border border-white/5"
        >
          <div class="grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <div class="text-[var(--sd-text-muted)]">Home Win</div>
              <div class="font-mono font-semibold text-emerald-400">
                {{ ((item.prediction?.home_win_prob || 0) * 100).toFixed(0) }}%
              </div>
            </div>
            <div>
              <div class="text-[var(--sd-text-muted)]">Draw</div>
              <div class="font-mono font-semibold text-amber-400">
                {{ ((item.prediction?.draw_prob || 0) * 100).toFixed(0) }}%
              </div>
            </div>
            <div>
              <div class="text-[var(--sd-text-muted)]">Away Win</div>
              <div class="font-mono font-semibold text-red-400">
                {{ ((item.prediction?.away_win_prob || 0) * 100).toFixed(0) }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <div v-else class="text-center py-6 text-[var(--sd-text-muted)]">
      No upcoming fixtures scheduled
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import type { UpcomingResponse } from '@/types'

const loading = ref(false)
const error = ref('')
const data = ref<UpcomingResponse | null>(null)
const expandedFixtures = ref(new Set<number>())

const toggleExpand = (fixtureId: number) => {
  if (expandedFixtures.value.has(fixtureId)) {
    expandedFixtures.value.delete(fixtureId)
  } else {
    expandedFixtures.value.add(fixtureId)
  }
}

const formatDate = (dateStr: string) => {
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.getUpcomingFixtures(2025, true)
    data.value = response.data || null
  } catch (e: any) {
    error.value = 'Failed to load upcoming fixtures'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
