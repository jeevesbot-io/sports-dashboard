<template>
  <div class="football-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h1>⚽ Premier League</h1>
      <p class="season">2025/26 Season</p>
    </div>

    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ standings.length }}</div>
        <div class="stat-label">Teams</div>
      </div>
      <div class="stat-card highlight">
        <div class="stat-value">{{ focusTeamPosition || '—' }}</div>
        <div class="stat-label">Newcastle Position</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ currentMatchday || '—' }}</div>
        <div class="stat-label">Current Matchday</div>
      </div>
      <div class="stat-card highlight">
        <div class="stat-value">{{ focusTeamPoints || '—' }}</div>
        <div class="stat-label">Newcastle Points</div>
      </div>
    </div>

    <!-- League Table -->
    <div class="table-section" v-if="standings.length">
      <h2>League Table</h2>
      <DataTable 
        :value="standings" 
        :rows="20"
        :rowClass="rowClass"
        sortMode="single"
        removableSort
        class="league-table"
        responsiveLayout="scroll"
      >
        <Column field="position" header="#" sortable :style="{ width: '50px' }"></Column>
        <Column header="Team" sortable sortField="team.short_name" :style="{ width: '200px' }">
          <template #body="{ data }">
            <router-link 
              :to="`/football/teams/${data.team.id}`" 
              class="team-link"
            >
              <div class="team-cell">
                <img 
                  :src="data.team.crest_url" 
                  :alt="data.team.short_name"
                  class="team-crest"
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
            <span :class="{ 'positive': data.goal_difference > 0, 'negative': data.goal_difference < 0 }">
              {{ data.goal_difference > 0 ? '+' : '' }}{{ data.goal_difference }}
            </span>
          </template>
        </Column>
        <Column field="points" header="Pts" sortable :style="{ width: '70px' }" class="points-column"></Column>
        <Column header="Form" :style="{ width: '120px' }">
          <template #body="{ data }">
            <div class="form-dots">
              <span 
                v-for="(result, index) in parseForm(data.form)" 
                :key="index"
                :class="['form-dot', getFormClass(result)]"
                :title="getFormTitle(result)"
              >
                {{ result }}
              </span>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Charts Section -->
    <div v-if="standings.length" class="charts-section">
      <div class="charts-grid">
        <div class="chart-item">
          <Card>
            <template #content>
              <PointsProgressionChart :standings="standings" />
            </template>
          </Card>
        </div>
        <div class="chart-item">
          <Card>
            <template #content>
              <GoalsComparisonChart :standings="standings" />
            </template>
          </Card>
        </div>
      </div>
      
      <div class="chart-full-width">
        <Card>
          <template #content>
            <FormHeatmapChart :standings="standings" />
          </template>
        </Card>
      </div>
    </div>

    <!-- Fixtures Section -->
    <div v-if="fixtures.length" class="fixtures-section">
      <Card>
        <template #content>
          <FixtureList :fixtures="fixtures" />
        </template>
      </Card>
    </div>

    <!-- Empty state -->
    <div v-else-if="!store.loading" class="empty-state">
      <p>No standings data yet. Run data ingestion to populate.</p>
    </div>

    <!-- Loading state -->
    <div v-if="store.loading" class="loading-state">
      <ProgressSpinner />
      <p>Loading football data...</p>
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

<style scoped>
.football-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.dashboard-header {
  margin-bottom: 2rem;
  text-align: center;
}

.dashboard-header h1 {
  margin: 0;
  color: #f0f0f0;
}

.season {
  color: #888;
  margin: 0.25rem 0 0 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #1e1e2e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 1.25rem;
  text-align: center;
}

.stat-card.highlight {
  border-color: #fff;
  background: #1a1a2a;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #f0f0f0;
}

.stat-label {
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.table-section {
  margin-bottom: 3rem;
}

.table-section h2 {
  color: #f0f0f0;
  margin-bottom: 1rem;
}

.team-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.team-crest {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.team-link {
  color: inherit;
  text-decoration: none;
}

.team-link:hover {
  color: #fff;
  text-decoration: underline;
}

.positive {
  color: #27ae60;
}

.negative {
  color: #e74c3c;
}

.form-dots {
  display: flex;
  gap: 2px;
  justify-content: center;
}

.form-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: white;
}

.form-dot.win {
  background: #27ae60;
}

.form-dot.draw {
  background: #f39c12;
}

.form-dot.loss {
  background: #e74c3c;
}

.charts-section {
  margin-bottom: 3rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.chart-full-width {
  width: 100%;
}

.fixtures-section {
  margin-bottom: 2rem;
}

.empty-state, .loading-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

/* Custom DataTable styling for dark theme */
:deep(.league-table) {
  background: transparent;
}

:deep(.league-table .p-datatable-thead > tr > th) {
  background: #1e1e2e;
  color: #888;
  border-color: #333;
  font-weight: 600;
}

:deep(.league-table .p-datatable-tbody > tr) {
  background: transparent;
  color: #ccc;
}

:deep(.league-table .p-datatable-tbody > tr:nth-child(even)) {
  background: rgba(255, 255, 255, 0.02);
}

:deep(.league-table .p-datatable-tbody > tr:hover) {
  background: rgba(255, 255, 255, 0.05);
}

:deep(.league-table .p-datatable-tbody > tr.focus-team-row) {
  background: rgba(255, 255, 255, 0.08) !important;
  font-weight: 600;
  color: #f0f0f0;
}

:deep(.league-table .p-datatable-tbody > tr > td) {
  border-color: #222;
  text-align: center;
}

:deep(.league-table .p-datatable-tbody > tr > td:first-child) {
  text-align: center;
  font-weight: 700;
}

:deep(.league-table .points-column) {
  font-weight: 700;
  color: #f0f0f0;
}

:deep(.league-table .p-sortable-column:hover) {
  background: rgba(255, 255, 255, 0.05);
}

:deep(.league-table .p-sortable-column-icon) {
  color: #666;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>