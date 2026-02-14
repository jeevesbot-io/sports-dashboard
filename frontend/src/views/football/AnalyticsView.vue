<!--
Advanced Football Analytics View
-->
<template>
  <div class="analytics-view">
    <!-- Header -->
    <div class="page-header mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold mb-2">Advanced Analytics</h1>
          <p class="text-gray-600">
            Deep dive into expected goals, head-to-head records, and match predictions
          </p>
        </div>
        <div class="flex gap-2">
          <Button
            @click="refreshData"
            :loading="loading"
            icon="pi pi-refresh"
            label="Refresh"
            severity="secondary"
            size="small"
          />
          <Button
            @click="ingestXGData"
            :loading="ingesting"
            icon="pi pi-download"
            label="Update xG Data"
            size="small"
          />
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <TabView v-model:activeIndex="activeTab" class="mb-4">
      <!-- Head-to-Head Tab -->
      <TabPanel header="Head-to-Head">
        <HeadToHead />
      </TabPanel>

      <!-- xG Analysis Tab -->
      <TabPanel header="xG Analysis">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- xG Table -->
          <Card class="col-span-1 lg:col-span-2">
            <template #title>
              <div class="flex justify-between items-center">
                <span>xG League Table</span>
                <Tag
                  v-if="mockDataUsed"
                  severity="warning"
                  value="Mock Data"
                  icon="pi pi-info-circle"
                />
              </div>
            </template>
            <template #content>
              <XgTable
                :data="xgStandings"
                :loading="loadingXG"
                @refresh="loadXGStandings"
              />
            </template>
          </Card>

          <!-- xG Chart -->
          <Card>
            <template #title>Performance vs xG</template>
            <template #content>
              <XgChart
                :data="xgStandings"
                :loading="loadingXG"
              />
            </template>
          </Card>

          <!-- Over/Under Performers -->
          <Card>
            <template #title>Over/Under Performers</template>
            <template #content>
              <div class="space-y-3">
                <div
                  v-for="team in overperformers"
                  :key="team.team"
                  class="flex justify-between items-center p-3 border rounded-lg"
                  :class="{
                    'bg-green-50 border-green-200': team.overperformance > 0,
                    'bg-red-50 border-red-200': team.overperformance < 0
                  }"
                >
                  <span class="font-medium">{{ team.team }}</span>
                  <div class="text-right">
                    <div class="text-sm text-gray-600">
                      {{ team.goals_for }}-{{ team.goals_against }} goals
                    </div>
                    <div class="text-sm text-gray-600">
                      {{ team.xg_for }}-{{ team.xg_against }} xG
                    </div>
                    <Tag
                      :value="`${team.overperformance > 0 ? '+' : ''}${team.overperformance}`"
                      :severity="team.overperformance > 0 ? 'success' : 'danger'"
                    />
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>
      </TabPanel>

      <!-- Predictions Tab -->
      <TabPanel header="Match Predictions">
        <MatchPredictor />
      </TabPanel>

      <!-- Charts Tab -->
      <TabPanel header="Charts">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <template #title>Points Progression</template>
            <template #content>
              <PointsProgressionChart
                :height="400"
                @error="handleChartError"
              />
            </template>
          </Card>

          <Card>
            <template #title>Form Heatmap</template>
            <template #content>
              <FormHeatmapChart
                :height="400"
                :games="10"
                @error="handleChartError"
              />
            </template>
          </Card>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'

// PrimeVue Components
import Button from 'primevue/button'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Tag from 'primevue/tag'

// Custom Components
import HeadToHead from '@/components/football/HeadToHead.vue'
import XgTable from '@/components/football/XgTable.vue'
import XgChart from '@/components/football/XgChart.vue'
import MatchPredictor from '@/components/football/MatchPredictor.vue'
import PointsProgressionChart from '@/components/football/PointsProgressionChart.vue'
import FormHeatmapChart from '@/components/football/FormHeatmapChart.vue'

// Services
import apiClient from '@/api'
import type { XGStanding } from '@/types'

// Reactive state
const toast = useToast()
const activeTab = ref(0)
const loading = ref(false)
const loadingXG = ref(false)
const ingesting = ref(false)
const mockDataUsed = ref(false)

const xgStandings = ref<XGStanding[]>([])
const overperformers = ref<XGStanding[]>([])

// Computed properties
const significantOverperformers = computed(() => {
  return overperformers.value.slice(0, 5) // Top 5
})

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

    // Check if mock data is being used
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

      // Refresh the data after ingestion
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

<style scoped>
.analytics-view {
  @apply container mx-auto px-4 py-6;
}

.page-header {
  @apply border-b pb-6;
}

:deep(.p-tabview-panels) {
  @apply p-0;
}

:deep(.p-tabview-panel) {
  @apply pt-4;
}
</style>