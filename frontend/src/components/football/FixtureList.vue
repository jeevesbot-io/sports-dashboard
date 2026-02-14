<template>
  <div class="fixture-list">
    <h3>Fixtures & Results</h3>
    <TabView>
      <TabPanel header="Recent Results">
        <div v-if="recentFixtures.length === 0" class="no-data">
          <p>No recent results available</p>
        </div>
        <div v-else class="fixtures">
          <div 
            v-for="fixture in recentFixtures" 
            :key="fixture.id"
            :class="['fixture-item', { 'newcastle-fixture': isNewcastleFixture(fixture) }]"
          >
            <div class="fixture-date">
              {{ formatDate(fixture.utc_date) }}
            </div>
            <div class="fixture-match">
              <span class="home-team">{{ fixture.home_team.short_name }}</span>
              <span class="score">{{ fixture.home_score }} - {{ fixture.away_score }}</span>
              <span class="away-team">{{ fixture.away_team.short_name }}</span>
            </div>
          </div>
        </div>
      </TabPanel>
      
      <TabPanel header="Upcoming">
        <div v-if="upcomingFixtures.length === 0" class="no-data">
          <p>No upcoming fixtures available</p>
        </div>
        <div v-else class="fixtures">
          <div 
            v-for="fixture in upcomingFixtures" 
            :key="fixture.id"
            :class="['fixture-item', { 'newcastle-fixture': isNewcastleFixture(fixture) }]"
          >
            <div class="fixture-date">
              {{ formatDate(fixture.utc_date) }}
            </div>
            <div class="fixture-match">
              <span class="home-team">{{ fixture.home_team.short_name }}</span>
              <span class="vs">vs</span>
              <span class="away-team">{{ fixture.away_team.short_name }}</span>
            </div>
          </div>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FootballFixture } from '@/types'

interface Props {
  fixtures: FootballFixture[]
}

const props = defineProps<Props>()

const recentFixtures = computed(() => {
  return props.fixtures
    .filter(f => f.status === 'FINISHED')
    .sort((a, b) => new Date(b.utc_date).getTime() - new Date(a.utc_date).getTime())
    .slice(0, 10)
})

const upcomingFixtures = computed(() => {
  return props.fixtures
    .filter(f => f.status === 'SCHEDULED')
    .sort((a, b) => new Date(a.utc_date).getTime() - new Date(b.utc_date).getTime())
    .slice(0, 10)
})

const isNewcastleFixture = (fixture: FootballFixture) => {
  return fixture.home_team.short_name === 'Newcastle' || 
         fixture.away_team.short_name === 'Newcastle'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  })
}
</script>

<style scoped>
.fixture-list h3 {
  margin: 0 0 1rem 0;
  color: #f0f0f0;
  font-size: 1.1rem;
  text-align: center;
}

.fixtures {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.fixture-item {
  background: #1e1e2e;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.fixture-item.newcastle-fixture {
  background: #1a1a2a;
  border-color: #444;
}

.fixture-date {
  min-width: 80px;
  color: #888;
  font-size: 0.85rem;
}

.fixture-match {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f0f0f0;
}

.home-team, .away-team {
  min-width: 80px;
}

.home-team {
  text-align: right;
}

.away-team {
  text-align: left;
}

.score {
  font-weight: 700;
  color: #fff;
  padding: 0 0.5rem;
}

.vs {
  color: #888;
  padding: 0 0.5rem;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.no-data p {
  margin: 0;
}

/* Custom TabView styling to match theme */
:deep(.p-tabview-nav) {
  background: #1e1e2e;
  border-color: #333;
}

:deep(.p-tabview-nav-link) {
  color: #888;
}

:deep(.p-tabview-nav-link:hover) {
  color: #f0f0f0;
}

:deep(.p-tabview-selected .p-tabview-nav-link) {
  color: #f0f0f0;
  border-color: #fff;
}

:deep(.p-tabview-panels) {
  background: transparent;
  border: 1px solid #333;
  border-top: none;
  padding: 1rem;
}
</style>