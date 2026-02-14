<template>
  <div class="football-dashboard">
    <div class="dashboard-header">
      <h1>⚽ Premier League</h1>
      <p class="season">2025/26 Season</p>
    </div>

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
        <div class="stat-label">Matchday</div>
      </div>
    </div>

    <div class="table-section" v-if="standings.length">
      <h2>League Table</h2>
      <div class="table-wrapper">
        <table class="league-table">
          <thead>
            <tr>
              <th>#</th>
              <th class="team-col">Team</th>
              <th>P</th>
              <th>W</th>
              <th>D</th>
              <th>L</th>
              <th>GF</th>
              <th>GA</th>
              <th>GD</th>
              <th>Pts</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="team in standings" :key="team.team_id"
                :class="{ 'focus-team': team.short_name === 'Newcastle' }">
              <td>{{ team.position }}</td>
              <td class="team-col">
                <router-link :to="`/football/teams/${team.team_id}`" class="team-link">
                  {{ team.short_name }}
                </router-link>
              </td>
              <td>{{ team.played }}</td>
              <td>{{ team.won }}</td>
              <td>{{ team.drawn }}</td>
              <td>{{ team.lost }}</td>
              <td>{{ team.goals_for }}</td>
              <td>{{ team.goals_against }}</td>
              <td>{{ team.goal_difference }}</td>
              <td class="points">{{ team.points }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>No standings data yet. Run data ingestion to populate.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useFootballStore } from '@/stores/football'

const store = useFootballStore()

const standings = computed(() => store.standings)
const currentMatchday = computed(() => {
  if (standings.value.length === 0) return null
  return Math.max(...standings.value.map((s: any) => s.played))
})
const focusTeamPosition = computed(() => {
  const newcastle = standings.value.find((s: any) => s.short_name === 'Newcastle')
  return newcastle?.position
})

onMounted(() => {
  store.fetchStandings()
})
</script>

<style scoped>
.football-dashboard {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1.5rem;
}

.dashboard-header {
  margin-bottom: 2rem;
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
  grid-template-columns: repeat(3, 1fr);
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

.table-section h2 {
  color: #f0f0f0;
  margin-bottom: 1rem;
}

.table-wrapper {
  overflow-x: auto;
}

.league-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.league-table th {
  background: #1e1e2e;
  color: #888;
  font-weight: 600;
  padding: 0.75rem 0.5rem;
  text-align: center;
  border-bottom: 2px solid #333;
}

.league-table th.team-col,
.league-table td.team-col {
  text-align: left;
  padding-left: 1rem;
}

.league-table td {
  padding: 0.6rem 0.5rem;
  text-align: center;
  border-bottom: 1px solid #222;
  color: #ccc;
}

.league-table tr:hover {
  background: rgba(255,255,255,0.03);
}

.league-table tr.focus-team {
  background: rgba(255,255,255,0.06);
  font-weight: 600;
}

.league-table tr.focus-team td {
  color: #f0f0f0;
}

.team-link {
  color: inherit;
  text-decoration: none;
}

.team-link:hover {
  text-decoration: underline;
}

.points {
  font-weight: 700;
  color: #f0f0f0;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}
</style>
