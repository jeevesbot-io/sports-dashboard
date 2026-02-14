<template>
  <div class="team-detail">
    <!-- Back Button -->
    <Button 
      icon="pi pi-arrow-left" 
      label="Back to League Table" 
      text 
      @click="$router.push('/football')"
      class="back-button"
    />

    <!-- Loading State -->
    <div v-if="store.loading" class="loading-state">
      <ProgressSpinner />
      <p>Loading team details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="error-state">
      <p>{{ store.error }}</p>
      <Button label="Retry" @click="loadTeamData" />
    </div>

    <!-- Team Details -->
    <div v-else-if="selectedTeam" class="team-content">
      <!-- Team Header -->
      <div class="team-header">
        <div class="team-info">
          <img 
            :src="selectedTeam.crest_url" 
            :alt="selectedTeam.name"
            class="team-crest-large"
            @error="handleImageError"
          />
          <div class="team-names">
            <h1>{{ selectedTeam.name }}</h1>
            <p class="team-short">{{ selectedTeam.short_name }} ({{ selectedTeam.tla }})</p>
          </div>
        </div>
      </div>

      <!-- Season Statistics -->
      <div class="stats-section">
        <h2>Season Statistics</h2>
        <div class="stats-grid">
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.position || '—' }}</div>
                <div class="stat-label">League Position</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.points || 0 }}</div>
                <div class="stat-label">Points</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.played || 0 }}</div>
                <div class="stat-label">Played</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.won || 0 }}</div>
                <div class="stat-label">Won</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.drawn || 0 }}</div>
                <div class="stat-label">Drawn</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.lost || 0 }}</div>
                <div class="stat-label">Lost</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.goals_for || 0 }}</div>
                <div class="stat-label">Goals For</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">{{ teamStanding?.goals_against || 0 }}</div>
                <div class="stat-label">Goals Against</div>
              </div>
            </template>
          </Card>
          
          <Card class="stat-card">
            <template #content>
              <div class="stat-item">
                <div class="stat-value">
                  <span :class="{ 'positive': goalDifference > 0, 'negative': goalDifference < 0 }">
                    {{ goalDifference > 0 ? '+' : '' }}{{ goalDifference }}
                  </span>
                </div>
                <div class="stat-label">Goal Difference</div>
              </div>
            </template>
          </Card>
        </div>
      </div>

      <!-- Recent Form -->
      <div class="form-section" v-if="teamStanding?.form">
        <h2>Recent Form</h2>
        <Card>
          <template #content>
            <div class="form-display">
              <div class="form-dots">
                <span 
                  v-for="(result, index) in parseForm(teamStanding.form)" 
                  :key="index"
                  :class="['form-dot', getFormClass(result)]"
                  :title="getFormTitle(result)"
                >
                  {{ result }}
                </span>
              </div>
              <div class="form-stats">
                <div class="form-stat">
                  <span class="form-stat-value">{{ formStats.wins }}</span>
                  <span class="form-stat-label">Wins</span>
                </div>
                <div class="form-stat">
                  <span class="form-stat-value">{{ formStats.draws }}</span>
                  <span class="form-stat-label">Draws</span>
                </div>
                <div class="form-stat">
                  <span class="form-stat-value">{{ formStats.losses }}</span>
                  <span class="form-stat-label">Losses</span>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Additional Info -->
      <div class="additional-info">
        <Card>
          <template #content>
            <div class="info-grid">
              <div class="info-item">
                <strong>Win Percentage:</strong> 
                {{ teamStanding ? (teamStanding.win_percentage || 0).toFixed(1) : 0 }}%
              </div>
              <div class="info-item">
                <strong>Points per Game:</strong> 
                {{ teamStanding ? (teamStanding.points_per_game || 0).toFixed(2) : 0 }}
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Not Found State -->
    <div v-else class="not-found-state">
      <h2>Team Not Found</h2>
      <p>The requested team could not be found.</p>
      <Button label="Go Back" @click="$router.push('/football')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFootballStore } from '@/stores/football'

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

<style scoped>
.team-detail {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1.5rem;
}

.back-button {
  margin-bottom: 2rem;
}

.loading-state, .error-state, .not-found-state {
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

.team-header {
  margin-bottom: 2rem;
}

.team-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.team-crest-large {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

.team-names h1 {
  margin: 0;
  color: #f0f0f0;
  font-size: 2rem;
}

.team-short {
  color: #888;
  margin: 0.5rem 0 0 0;
  font-size: 1.1rem;
}

.stats-section {
  margin-bottom: 2rem;
}

.stats-section h2 {
  color: #f0f0f0;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #f0f0f0;
}

.stat-label {
  color: #888;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h2 {
  color: #f0f0f0;
  margin-bottom: 1rem;
}

.form-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.form-dots {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.form-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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

.form-stats {
  display: flex;
  gap: 2rem;
}

.form-stat {
  text-align: center;
}

.form-stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #f0f0f0;
}

.form-stat-label {
  color: #888;
  font-size: 0.9rem;
}

.additional-info {
  margin-bottom: 2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  color: #f0f0f0;
}

.positive {
  color: #27ae60;
}

.negative {
  color: #e74c3c;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .team-info {
    flex-direction: column;
    text-align: center;
  }
  
  .form-stats {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>