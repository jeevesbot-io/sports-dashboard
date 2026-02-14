<template>
  <div class="max-w-[1200px] mx-auto">
    <!-- Page Header -->
    <div class="flex items-center gap-4 mb-8">
      <h1 class="font-display text-3xl font-bold text-[var(--sd-text-primary)]">Premier League</h1>
      <GradientBadge label="2025/26" variant="new" size="md" />
      <GradientBadge v-if="currentMatchday" :label="`MD ${currentMatchday}`" variant="default" size="md" />
    </div>

    <!-- Loading State -->
    <div v-if="store.loading" class="space-y-6">
      <SkeletonLoader variant="stat-row" :cols="4" />
      <SkeletonLoader variant="table" :rows="10" />
    </div>

    <template v-else-if="standings.length">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div style="animation-delay: 0ms">
          <StatCard
            :value="standings.length"
            label="Teams"
            icon="pi pi-users"
            gradient="var(--sd-gradient-1)"
          />
        </div>
        <div style="animation-delay: 50ms">
          <StatCard
            :value="focusTeamPosition || '—'"
            label="Newcastle Position"
            icon="pi pi-hashtag"
            gradient="var(--sd-gradient-2)"
          />
        </div>
        <div style="animation-delay: 100ms">
          <StatCard
            :value="currentMatchday || '—'"
            label="Current Matchday"
            icon="pi pi-calendar"
            gradient="var(--sd-gradient-3)"
          />
        </div>
        <div style="animation-delay: 150ms">
          <StatCard
            :value="focusTeamPoints || '—'"
            label="Newcastle Points"
            icon="pi pi-star"
            gradient="var(--sd-gradient-4)"
          />
        </div>
      </div>

      <!-- League Table -->
      <GlassCard class="mb-8">
        <template #header>
          <h2 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">League Table</h2>
        </template>
        <DataTable
          :value="standings"
          :rows="20"
          :rowClass="rowClass"
          sortMode="single"
          removableSort
          class="league-table"
          responsiveLayout="scroll"
        >
          <Column field="position" header="#" sortable :style="{ width: '50px' }">
            <template #body="{ data }">
              <span
                class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold"
                :class="{
                  'bg-cyan-500/20 text-cyan-300': data.position <= 4,
                  'bg-red-500/20 text-red-400': data.position >= 18,
                  'text-[var(--sd-text-secondary)]': data.position > 4 && data.position < 18
                }"
              >
                {{ data.position }}
              </span>
            </template>
          </Column>
          <Column header="Team" sortable sortField="team.short_name" :style="{ width: '200px' }">
            <template #body="{ data }">
              <router-link
                :to="`/football/teams/${data.team.id}`"
                class="text-[var(--sd-text-primary)] no-underline hover:text-white transition-colors"
              >
                <div class="flex items-center gap-2">
                  <img
                    :src="data.team.crest_url"
                    :alt="data.team.short_name"
                    class="w-5 h-5 shrink-0 object-contain"
                    @error="handleImageError"
                  />
                  <span>{{ data.team.short_name }}</span>
                </div>
              </router-link>
            </template>
          </Column>
          <Column field="played" header="P" sortable :style="{ width: '60px' }"></Column>
          <Column field="won" header="W" sortable :style="{ width: '60px' }"></Column>
          <Column field="drawn" header="D" sortable :style="{ width: '60px' }"></Column>
          <Column field="lost" header="L" sortable :style="{ width: '60px' }"></Column>
          <Column field="goals_for" header="GF" sortable :style="{ width: '70px' }"></Column>
          <Column field="goals_against" header="GA" sortable :style="{ width: '70px' }"></Column>
          <Column field="goal_difference" header="GD" sortable :style="{ width: '70px' }">
            <template #body="{ data }">
              <span :class="{
                'text-emerald-400': data.goal_difference > 0,
                'text-red-400': data.goal_difference < 0,
                'text-[var(--sd-text-muted)]': data.goal_difference === 0
              }">
                {{ data.goal_difference > 0 ? '+' : '' }}{{ data.goal_difference }}
              </span>
            </template>
          </Column>
          <Column field="points" header="Pts" sortable :style="{ width: '70px' }">
            <template #body="{ data }">
              <span class="font-bold text-[var(--sd-text-primary)]">{{ data.points }}</span>
            </template>
          </Column>
          <Column header="Form" :style="{ width: '180px' }">
            <template #body="{ data }">
              <div class="flex gap-1 justify-center">
                <span
                  v-for="(result, index) in parseForm(data.form)"
                  :key="index"
                  :class="['form-dot', `form-dot-${getFormClass(result)}`]"
                  :title="getFormTitle(result)"
                >
                  {{ result }}
                </span>
              </div>
            </template>
          </Column>
        </DataTable>
      </GlassCard>

      <!-- Upcoming Matches -->
      <div class="mb-8">
        <GlassCard>
          <UpcomingMatchesPanel />
        </GlassCard>
      </div>

      <!-- Newcastle Focus Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartCard title="Newcastle vs League Average">
          <TeamVsLeague />
        </ChartCard>
        <ChartCard title="Season Tracker">
          <SeasonTracker />
        </ChartCard>
      </div>

      <!-- Charts Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartCard title="Points Progression">
          <PointsProgressionChart />
        </ChartCard>
        <ChartCard title="Goals Comparison">
          <GoalsComparisonChart :standings="standings" />
        </ChartCard>
      </div>

      <div class="mb-8">
        <ChartCard title="Form Heatmap">
          <FormHeatmapChart :standings="standings" />
        </ChartCard>
      </div>

      <!-- Fixtures Section -->
      <div v-if="fixtures.length" class="mb-8">
        <GlassCard>
          <template #header>
            <h2 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Fixtures</h2>
          </template>
          <FixtureList :fixtures="fixtures" />
        </GlassCard>
      </div>
    </template>

    <!-- Empty State -->
    <div v-else class="text-center py-16">
      <i class="pi pi-inbox text-4xl text-[var(--sd-text-muted)] mb-4"></i>
      <p class="text-[var(--sd-text-muted)]">No standings data yet. Run data ingestion to populate.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useFootballStore } from '@/stores/football'
import PointsProgressionChart from '@/components/football/PointsProgressionChart.vue'
import GoalsComparisonChart from '@/components/football/GoalsComparisonChart.vue'
import FormHeatmapChart from '@/components/football/FormHeatmapChart.vue'
import FixtureList from '@/components/football/FixtureList.vue'
import TeamVsLeague from '@/components/football/TeamVsLeague.vue'
import SeasonTracker from '@/components/football/SeasonTracker.vue'
import UpcomingMatchesPanel from '@/components/football/UpcomingMatchesPanel.vue'
import StatCard from '@/components/ui/StatCard.vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import ChartCard from '@/components/ui/ChartCard.vue'
import GradientBadge from '@/components/ui/GradientBadge.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'

const store = useFootballStore()

const standings = computed(() => store.standings)
const fixtures = computed(() => store.fixtures)

const currentMatchday = computed(() => {
  if (standings.value.length === 0) return null
  return Math.max(...standings.value.map((s: any) => s.played))
})

const focusTeamPosition = computed(() => {
  const newcastle = standings.value.find((s: any) => s.team.short_name === 'Newcastle')
  return newcastle?.position
})

const focusTeamPoints = computed(() => {
  const newcastle = standings.value.find((s: any) => s.team.short_name === 'Newcastle')
  return newcastle?.points
})

const rowClass = (data: any) => {
  return data.team.short_name === 'Newcastle' ? 'focus-team-row' : ''
}

const parseForm = (form: string) => {
  if (!form) return []
  return form.split(',').map(f => f.trim()).slice(0, 5)
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

onMounted(async () => {
  await store.fetchStandings()
  // Fetch all fixtures in one call — FixtureList splits by status internally
  try {
    await store.fetchFixtures({ limit: 50 })
  } catch (error) {
    console.warn('Could not fetch fixtures:', error)
  }
})
</script>
