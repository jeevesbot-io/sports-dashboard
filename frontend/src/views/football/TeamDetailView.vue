<template>
  <div class="max-w-[1000px] mx-auto">
    <!-- Back Button -->
    <button
      @click="$router.push('/football')"
      class="flex items-center gap-2 text-[var(--sd-text-muted)] hover:text-[var(--sd-text-primary)] transition-colors mb-6"
    >
      <i class="pi pi-arrow-left text-sm"></i>
      <span class="text-sm font-medium">Back to League Table</span>
    </button>

    <!-- Loading State -->
    <div v-if="store.loading" class="space-y-6">
      <SkeletonLoader variant="card" />
      <SkeletonLoader variant="stat-row" :cols="3" />
      <SkeletonLoader variant="stat-row" :cols="3" />
      <SkeletonLoader variant="stat-row" :cols="3" />
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="text-center py-16">
      <i class="pi pi-exclamation-triangle text-4xl text-[var(--sd-loss)] mb-4"></i>
      <p class="text-[var(--sd-text-muted)] mb-4">{{ store.error }}</p>
      <button @click="loadTeamData" class="pill-nav-item pill-nav-item-active">Retry</button>
    </div>

    <!-- Team Details -->
    <div v-else-if="selectedTeam">
      <!-- Hero Banner -->
      <div class="glass-card p-8 min-h-[200px] relative overflow-hidden mb-8">
        <div
          class="absolute inset-0 opacity-10"
          style="background: linear-gradient(135deg, var(--sd-accent-cyan), var(--sd-accent-violet))"
        ></div>
        <div class="relative z-10 flex items-center gap-6">
          <img
            :src="selectedTeam.crest_url"
            :alt="selectedTeam.name"
            class="w-24 h-24 object-contain"
            @error="handleImageError"
          />
          <div>
            <h1 class="font-display text-4xl font-bold text-[var(--sd-text-primary)]">{{ selectedTeam.name }}</h1>
            <p class="text-[var(--sd-text-muted)] text-lg mt-1">{{ selectedTeam.short_name }} ({{ selectedTeam.tla }})</p>
          </div>
        </div>
      </div>

      <!-- Season Statistics - 9 cards in 3-col grid -->
      <h2 class="font-display text-xl font-semibold text-[var(--sd-text-primary)] mb-4">Season Statistics</h2>
      <div class="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          :value="teamStanding?.position || '—'"
          label="League Position"
          icon="pi pi-hashtag"
          gradient="var(--sd-gradient-1)"
        />
        <StatCard
          :value="teamStanding?.points || 0"
          label="Points"
          icon="pi pi-star"
          gradient="var(--sd-gradient-2)"
        />
        <StatCard
          :value="teamStanding?.played || 0"
          label="Played"
          icon="pi pi-calendar"
          gradient="var(--sd-gradient-3)"
        />
        <StatCard
          :value="teamStanding?.won || 0"
          label="Won"
          icon="pi pi-check-circle"
          gradient="var(--sd-gradient-4)"
        />
        <StatCard
          :value="teamStanding?.drawn || 0"
          label="Drawn"
          icon="pi pi-minus-circle"
          gradient="var(--sd-gradient-1)"
        />
        <StatCard
          :value="teamStanding?.lost || 0"
          label="Lost"
          icon="pi pi-times-circle"
          gradient="var(--sd-gradient-2)"
        />
        <StatCard
          :value="teamStanding?.goals_for || 0"
          label="Goals For"
          icon="pi pi-arrow-up-right"
          gradient="var(--sd-gradient-3)"
        />
        <StatCard
          :value="teamStanding?.goals_against || 0"
          label="Goals Against"
          icon="pi pi-arrow-down-left"
          gradient="var(--sd-gradient-4)"
        />
        <div class="stat-card-glass relative overflow-hidden" style="background: var(--sd-gradient-1)">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-3">
              <span class="text-white/70 text-xs font-semibold uppercase tracking-wider">Goal Difference</span>
              <i class="pi pi-sort-alt text-white/20 text-2xl"></i>
            </div>
            <div class="flex items-end gap-3">
              <span
                class="font-display text-stat-2xl font-bold leading-none"
                :class="{
                  'text-emerald-300': goalDifference > 0,
                  'text-red-300': goalDifference < 0,
                  'text-white': goalDifference === 0
                }"
              >
                {{ goalDifference > 0 ? '+' : '' }}{{ goalDifference }}
              </span>
            </div>
          </div>
          <i class="pi pi-sort-alt absolute -bottom-2 -right-2 text-white/5 text-7xl pointer-events-none"></i>
        </div>
      </div>

      <!-- Recent Form -->
      <div v-if="teamStanding?.form" class="mb-8">
        <GlassCard>
          <template #header>
            <h2 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Recent Form</h2>
          </template>
          <div class="flex flex-col items-center gap-6 py-4">
            <div class="flex gap-2 flex-wrap justify-center">
              <span
                v-for="(result, index) in parseForm(teamStanding.form)"
                :key="index"
                :class="['form-dot', `form-dot-${getFormClass(result)}`]"
                :title="getFormTitle(result)"
                style="width: 28px; height: 28px; font-size: 12px;"
              >
                {{ result }}
              </span>
            </div>
            <div class="flex gap-8">
              <div class="text-center">
                <span class="block font-display text-2xl font-bold text-[var(--sd-text-primary)]">{{ formStats.wins }}</span>
                <span class="text-sm text-[var(--sd-text-muted)]">Wins</span>
              </div>
              <div class="text-center">
                <span class="block font-display text-2xl font-bold text-[var(--sd-text-primary)]">{{ formStats.draws }}</span>
                <span class="text-sm text-[var(--sd-text-muted)]">Draws</span>
              </div>
              <div class="text-center">
                <span class="block font-display text-2xl font-bold text-[var(--sd-text-primary)]">{{ formStats.losses }}</span>
                <span class="text-sm text-[var(--sd-text-muted)]">Losses</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>

      <!-- Opponent-Adjusted Form -->
      <div v-if="selectedTeam" class="mb-8">
        <GlassCard>
          <template #header>
            <h2 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Opponent-Adjusted Form</h2>
          </template>
          <FormRatingCard :teamId="selectedTeam.id" />
        </GlassCard>
      </div>

      <!-- Scoreline Frequency -->
      <div v-if="selectedTeam" class="mb-8">
        <ChartCard title="Most Common Scorelines">
          <ScorelineFrequencyChart :teamId="selectedTeam.id" />
        </ChartCard>
      </div>

      <!-- Additional Info -->
      <GlassCard>
        <template #header>
          <h2 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Additional Info</h2>
        </template>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex justify-between items-center p-3 rounded-xl bg-white/5">
            <span class="text-[var(--sd-text-muted)] text-sm">Win Percentage</span>
            <span class="font-mono font-semibold text-[var(--sd-text-primary)]">
              {{ teamStanding ? (teamStanding.win_percentage || 0).toFixed(1) : 0 }}%
            </span>
          </div>
          <div class="flex justify-between items-center p-3 rounded-xl bg-white/5">
            <span class="text-[var(--sd-text-muted)] text-sm">Points per Game</span>
            <span class="font-mono font-semibold text-[var(--sd-text-primary)]">
              {{ teamStanding ? (teamStanding.points_per_game || 0).toFixed(2) : 0 }}
            </span>
          </div>
        </div>
      </GlassCard>
    </div>

    <!-- Not Found State -->
    <div v-else class="text-center py-16">
      <i class="pi pi-search text-4xl text-[var(--sd-text-muted)] mb-4"></i>
      <h2 class="font-display text-xl font-semibold text-[var(--sd-text-primary)] mb-2">Team Not Found</h2>
      <p class="text-[var(--sd-text-muted)] mb-4">The requested team could not be found.</p>
      <button @click="$router.push('/football')" class="pill-nav-item pill-nav-item-active">Go Back</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFootballStore } from '@/stores/football'
import StatCard from '@/components/ui/StatCard.vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import ChartCard from '@/components/ui/ChartCard.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'
import FormRatingCard from '@/components/football/FormRatingCard.vue'
import ScorelineFrequencyChart from '@/components/football/ScorelineFrequencyChart.vue'

const route = useRoute()
const store = useFootballStore()

const selectedTeam = computed(() => store.selectedTeam)
const teamStanding = computed(() => {
  const teamId = parseInt(route.params.id as string)
  return store.standings.find(s => s.team.id === teamId)
})

const goalDifference = computed(() => {
  return (teamStanding.value?.goals_for || 0) - (teamStanding.value?.goals_against || 0)
})

const formStats = computed(() => {
  const form = teamStanding.value?.form
  if (!form) return { wins: 0, draws: 0, losses: 0 }

  const results = form.split(',').map(r => r.trim())
  return {
    wins: results.filter(r => r.toUpperCase() === 'W').length,
    draws: results.filter(r => r.toUpperCase() === 'D').length,
    losses: results.filter(r => r.toUpperCase() === 'L').length
  }
})

const parseForm = (form: string) => {
  if (!form) return []
  return form.split(',').map(f => f.trim()).slice(0, 10)
}

const getFormClass = (result: string) => {
  switch (result.toUpperCase()) {
    case 'W': return 'win'
    case 'D': return 'draw'
    case 'L': return 'loss'
    default: return ''
  }
}

const getFormTitle = (result: string) => {
  switch (result.toUpperCase()) {
    case 'W': return 'Win'
    case 'D': return 'Draw'
    case 'L': return 'Loss'
    default: return 'Unknown'
  }
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}

const loadTeamData = async () => {
  const teamId = parseInt(route.params.id as string)
  if (teamId) {
    try {
      await store.fetchTeamDetail(teamId)
    } catch (error) {
      console.error('Failed to load team details:', error)
    }
  }
}

// Watch route changes
watch(() => route.params.id, loadTeamData, { immediate: true })

onMounted(async () => {
  // Ensure we have standings data
  if (store.standings.length === 0) {
    await store.fetchStandings()
  }
  await loadTeamData()
})
</script>
