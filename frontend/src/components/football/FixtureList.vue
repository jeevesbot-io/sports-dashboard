<template>
  <div class="fixture-list">
    <h3 class="font-display text-lg font-semibold text-[var(--sd-text-primary)] mb-4 text-center">Fixtures & Results</h3>

    <!-- Two-column layout instead of TabView -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Results -->
      <div>
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Recent Results</div>
        <div v-if="recentFixtures.length === 0" class="text-center py-8 text-[var(--sd-text-muted)]">
          <p>No recent results available</p>
        </div>
        <div v-else class="flex flex-col gap-2 max-h-[350px] overflow-y-auto">
          <div
            v-for="fixture in recentFixtures"
            :key="fixture.id"
            :class="[
              'glass-card px-4 py-3 flex items-center gap-3',
              isNewcastleFixture(fixture) ? 'focus-team-row' : ''
            ]"
            style="border-radius: 10px"
          >
            <div class="text-xs text-[var(--sd-text-muted)] min-w-[70px]">
              {{ formatDate(fixture.utc_date) }}
            </div>
            <div class="flex-1 flex items-center justify-center gap-2 text-sm">
              <span class="text-right min-w-[80px] font-medium text-[var(--sd-text-primary)]">{{ fixture.home_team.short_name }}</span>
              <span class="font-mono font-bold text-[var(--sd-text-primary)] px-2 py-0.5 rounded bg-[var(--sd-surface-200)] text-xs">
                {{ fixture.home_score }} - {{ fixture.away_score }}
              </span>
              <span class="min-w-[80px] font-medium text-[var(--sd-text-primary)]">{{ fixture.away_team.short_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Upcoming -->
      <div>
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--sd-text-muted)] mb-3">Upcoming</div>
        <div v-if="upcomingFixtures.length === 0" class="text-center py-8 text-[var(--sd-text-muted)]">
          <p>No upcoming fixtures available</p>
        </div>
        <div v-else class="flex flex-col gap-2 max-h-[350px] overflow-y-auto">
          <div
            v-for="fixture in upcomingFixtures"
            :key="fixture.id"
            :class="[
              'glass-card px-4 py-3 flex items-center gap-3',
              isNewcastleFixture(fixture) ? 'focus-team-row' : ''
            ]"
            style="border-radius: 10px"
          >
            <div class="text-xs text-[var(--sd-text-muted)] min-w-[70px]">
              {{ formatDate(fixture.utc_date) }}
            </div>
            <div class="flex-1 flex items-center justify-center gap-2 text-sm">
              <span class="text-right min-w-[80px] font-medium text-[var(--sd-text-primary)]">{{ fixture.home_team.short_name }}</span>
              <span class="text-[var(--sd-text-muted)] text-xs px-2">vs</span>
              <span class="min-w-[80px] font-medium text-[var(--sd-text-primary)]">{{ fixture.away_team.short_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
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
