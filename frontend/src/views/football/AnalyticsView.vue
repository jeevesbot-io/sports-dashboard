<!--
Advanced Football Analytics View
-->
<template>
  <div class="max-w-[1400px] mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
      <div>
        <h1 class="font-display text-3xl font-bold text-[var(--sd-text-primary)]">Advanced Analytics</h1>
        <p class="text-[var(--sd-text-muted)] mt-1">
          Deep dive into expected goals, head-to-head records, match predictions, and more
        </p>
      </div>
      <div class="flex gap-2 shrink-0">
        <button
          @click="refreshData"
          :disabled="loading"
          class="pill-nav-item flex items-center gap-2 text-sm"
        >
          <i class="pi pi-refresh" :class="{ 'animate-spin': loading }"></i>
          Refresh
        </button>
        <button
          @click="ingestXGData"
          :disabled="ingesting"
          class="pill-nav-item pill-nav-item-active flex items-center gap-2 text-sm"
        >
          <i class="pi pi-download" :class="{ 'animate-spin': ingesting }"></i>
          Update xG
        </button>
        <button
          @click="ingestPlayerData"
          :disabled="ingestingPlayers"
          class="pill-nav-item flex items-center gap-2 text-sm"
        >
          <i class="pi pi-users" :class="{ 'animate-spin': ingestingPlayers }"></i>
          Players
        </button>
        <button
          @click="ingestFBrefData"
          :disabled="ingestingFBref"
          class="pill-nav-item flex items-center gap-2 text-sm"
        >
          <i class="pi pi-database" :class="{ 'animate-spin': ingestingFBref }"></i>
          FBref
        </button>
      </div>
    </div>

    <!-- Pill Navigation -->
    <div class="pill-nav mb-8 overflow-x-auto">
      <button
        v-for="(tab, index) in tabs"
        :key="tab.label"
        :class="['pill-nav-item', { 'pill-nav-item-active': activeTab === index }]"
        @click="activeTab = index"
      >
        <i :class="tab.icon" class="mr-1.5"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Panels -->

    <!-- Head-to-Head -->
    <div v-if="activeTab === 0">
      <GlassCard>
        <HeadToHead />
      </GlassCard>
    </div>

    <!-- xG Analysis -->
    <div v-if="activeTab === 1">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- xG Table -->
        <GlassCard class="col-span-1 lg:col-span-2">
          <template #header>
            <div class="flex justify-between items-center">
              <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">xG League Table</h3>
              <GradientBadge
                v-if="mockDataUsed"
                label="MOCK DATA"
                variant="mock"
              />
            </div>
          </template>
          <XgTable
            :data="xgStandings"
            :loading="loadingXG"
            @refresh="loadXGStandings"
          />
        </GlassCard>

        <!-- xG Chart -->
        <ChartCard title="Performance vs xG">
          <XgChart
            :data="xgStandings"
            :loading="loadingXG"
          />
        </ChartCard>

        <!-- Over/Under Performers -->
        <GlassCard>
          <template #header>
            <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Over/Under Performers</h3>
          </template>
          <div class="space-y-3">
            <div
              v-for="team in overperformers"
              :key="team.team"
              class="flex justify-between items-center p-3 rounded-xl border transition-colors"
              :class="{
                'border-emerald-500/20 bg-emerald-500/5': team.overperformance > 0,
                'border-red-500/20 bg-red-500/5': team.overperformance < 0
              }"
            >
              <span class="font-medium text-[var(--sd-text-primary)]">{{ team.team }}</span>
              <div class="text-right">
                <div class="text-sm text-[var(--sd-text-muted)]">
                  {{ team.goals_for }}-{{ team.goals_against }} goals
                </div>
                <div class="text-sm text-[var(--sd-text-muted)]">
                  {{ team.xg_for }}-{{ team.xg_against }} xG
                </div>
                <GradientBadge
                  :label="`${team.overperformance > 0 ? '+' : ''}${team.overperformance}`"
                  :variant="team.overperformance > 0 ? 'win' : 'loss'"
                />
              </div>
            </div>
          </div>
        </GlassCard>

        <!-- xG Timeline -->
        <ChartCard title="xG Over/Underperformance Timeline" class="col-span-1 lg:col-span-2">
          <XgTimeline />
        </ChartCard>
      </div>
    </div>

    <!-- Players -->
    <div v-if="activeTab === 2">
      <GlassCard>
        <template #header>
          <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Player Statistics</h3>
        </template>
        <PlayerDashboard />
      </GlassCard>
    </div>

    <!-- Home/Away -->
    <div v-if="activeTab === 3">
      <ChartCard title="Home Advantage Index">
        <HomeAdvantageChart />
      </ChartCard>
    </div>

    <!-- Projections -->
    <div v-if="activeTab === 4">
      <ChartCard title="Season Outcome Projections">
        <SeasonProjections />
      </ChartCard>
    </div>

    <!-- Advanced Stats -->
    <div v-if="activeTab === 5">
      <GlassCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Advanced Team Stats (FBref)</h3>
            <GradientBadge label="FBREF DATA" variant="new" />
          </div>
        </template>
        <AdvancedStatsTable />
      </GlassCard>
    </div>

    <!-- Predictions -->
    <div v-if="activeTab === 6">
      <div class="space-y-6">
        <GlassCard>
          <MatchPredictor />
        </GlassCard>
        <GlassCard>
          <template #header>
            <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)]">Prediction Performance</h3>
          </template>
          <PredictionAccuracyDashboard />
        </GlassCard>
      </div>
    </div>

    <!-- Charts -->
    <div v-if="activeTab === 7">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Points Progression" height="400px">
          <PointsProgressionChart
            :height="400"
            @error="handleChartError"
          />
        </ChartCard>

        <ChartCard title="Position Progression" height="500px">
          <PositionProgressionChart />
        </ChartCard>

        <ChartCard title="Form Heatmap" height="400px">
          <FormHeatmapChart
            :height="400"
            :games="10"
            @error="handleChartError"
          />
        </ChartCard>
      </div>
    </div>

    <!-- Fixture Difficulty -->
    <div v-if="activeTab === 8">
      <ChartCard title="Fixture Difficulty Heatmap">
        <FixtureDifficultyHeatmap />
      </ChartCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'

// UI Components
import GlassCard from '@/components/ui/GlassCard.vue'
import ChartCard from '@/components/ui/ChartCard.vue'
import GradientBadge from '@/components/ui/GradientBadge.vue'

// Custom Components
import HeadToHead from '@/components/football/HeadToHead.vue'
import XgTable from '@/components/football/XgTable.vue'
import XgChart from '@/components/football/XgChart.vue'
import XgTimeline from '@/components/football/XgTimeline.vue'
import MatchPredictor from '@/components/football/MatchPredictor.vue'
import PointsProgressionChart from '@/components/football/PointsProgressionChart.vue'
import FormHeatmapChart from '@/components/football/FormHeatmapChart.vue'
import HomeAdvantageChart from '@/components/football/HomeAdvantageChart.vue'
import PlayerDashboard from '@/components/football/PlayerDashboard.vue'
import SeasonProjections from '@/components/football/SeasonProjections.vue'
import AdvancedStatsTable from '@/components/football/AdvancedStatsTable.vue'
import FixtureDifficultyHeatmap from '@/components/football/FixtureDifficultyHeatmap.vue'
import PositionProgressionChart from '@/components/football/PositionProgressionChart.vue'
import PredictionAccuracyDashboard from '@/components/football/PredictionAccuracyDashboard.vue'

// Services
import apiClient from '@/api'
import type { XGStanding } from '@/types'

// Tab config
const tabs = [
  { label: 'Head-to-Head', icon: 'pi pi-arrows-h' },
  { label: 'xG Analysis', icon: 'pi pi-chart-scatter' },
  { label: 'Players', icon: 'pi pi-users' },
  { label: 'Home/Away', icon: 'pi pi-home' },
  { label: 'Projections', icon: 'pi pi-chart-line' },
  { label: 'Advanced', icon: 'pi pi-database' },
  { label: 'Predictions', icon: 'pi pi-calculator' },
  { label: 'Charts', icon: 'pi pi-chart-bar' },
  { label: 'Fixture Difficulty', icon: 'pi pi-th-large' },
]

// Reactive state
const toast = useToast()
const activeTab = ref(0)
const loading = ref(false)
const loadingXG = ref(false)
const ingesting = ref(false)
const ingestingPlayers = ref(false)
const ingestingFBref = ref(false)
const mockDataUsed = ref(false)

const xgStandings = ref<XGStanding[]>([])
const overperformers = ref<XGStanding[]>([])

// Methods
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadXGStandings(),
      loadOverperformers()
    ])
    toast.add({
      severity: 'success',
      summary: 'Data Refreshed',
      detail: 'Analytics data has been updated',
      life: 3000
    })
  } catch (error) {
    console.error('Error refreshing data:', error)
    toast.add({
      severity: 'error',
      summary: 'Refresh Failed',
      detail: 'Failed to refresh analytics data',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

const loadXGStandings = async () => {
  loadingXG.value = true
  try {
    const response = await apiClient.getXGStandings()
    xgStandings.value = response.data || []
    mockDataUsed.value = (response.data?.length ?? 0) > 0 &&
                        (response.message?.includes('mock') ?? false)
  } catch (error) {
    console.error('Error loading xG standings:', error)
    toast.add({
      severity: 'error',
      summary: 'Load Error',
      detail: 'Failed to load xG standings',
      life: 3000
    })
  } finally {
    loadingXG.value = false
  }
}

const loadOverperformers = async () => {
  try {
    const response = await apiClient.getXGOverperformers()
    overperformers.value = response.data || []
  } catch (error) {
    console.error('Error loading overperformers:', error)
  }
}

const ingestXGData = async () => {
  ingesting.value = true
  try {
    const response = await apiClient.ingestXGData()
    if (response.success) {
      toast.add({
        severity: 'success',
        summary: 'xG Data Updated',
        detail: `Processed ${(response.data as any)?.stored_matches ?? 0} matches`,
        life: 5000
      })
      await loadXGStandings()
      await loadOverperformers()
    } else {
      toast.add({
        severity: 'warn',
        summary: 'Using Mock Data',
        detail: 'Scraping failed, using simulated xG data',
        life: 5000
      })
    }
  } catch (error) {
    console.error('Error ingesting xG data:', error)
    toast.add({
      severity: 'error',
      summary: 'Ingestion Failed',
      detail: 'Failed to update xG data',
      life: 3000
    })
  } finally {
    ingesting.value = false
  }
}

const ingestPlayerData = async () => {
  ingestingPlayers.value = true
  try {
    const response = await apiClient.ingestPlayerData()
    toast.add({
      severity: response.success ? 'success' : 'warn',
      summary: 'Player Data Updated',
      detail: `Stored ${(response.data as any)?.stored_players ?? 0} players`,
      life: 5000
    })
  } catch (error) {
    console.error('Error ingesting player data:', error)
    toast.add({ severity: 'error', summary: 'Failed', detail: 'Player ingestion failed', life: 3000 })
  } finally {
    ingestingPlayers.value = false
  }
}

const ingestFBrefData = async () => {
  ingestingFBref.value = true
  try {
    const response = await apiClient.ingestFBrefData()
    toast.add({
      severity: response.success ? 'success' : 'warn',
      summary: 'FBref Data Updated',
      detail: `Stored ${(response.data as any)?.team_stats_stored ?? 0} team stats, ${(response.data as any)?.player_stats_stored ?? 0} player stats`,
      life: 5000
    })
  } catch (error) {
    console.error('Error ingesting FBref data:', error)
    toast.add({ severity: 'error', summary: 'Failed', detail: 'FBref ingestion failed', life: 3000 })
  } finally {
    ingestingFBref.value = false
  }
}

const handleChartError = (error: any) => {
  console.error('Chart error:', error)
  toast.add({
    severity: 'error',
    summary: 'Chart Error',
    detail: 'Failed to load chart data',
    life: 3000
  })
}

// Lifecycle
onMounted(() => {
  refreshData()
})
</script>
