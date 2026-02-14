<template>
  <header class="bg-surface-800 border-b border-surface-700 shadow-lg">
    <div class="container mx-auto px-4 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo and Title -->
        <div class="flex items-center space-x-4">
          <router-link 
            to="/" 
            class="flex items-center space-x-3 hover:opacity-80 transition-opacity"
          >
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <i class="pi pi-chart-line text-white text-xl"></i>
            </div>
            <div>
              <h1 class="text-2xl font-bold text-surface-0">Sports Dashboard</h1>
              <p class="text-sm text-surface-400">Multi-Sport Analytics Platform</p>
            </div>
          </router-link>
        </div>
        
        <!-- Header Actions -->
        <div class="flex items-center space-x-4">
          <!-- Health Status Indicator -->
          <div class="flex items-center space-x-2">
            <div 
              :class="[
                'w-3 h-3 rounded-full',
                isOnline ? 'bg-green-500' : 'bg-red-500'
              ]"
            ></div>
            <span class="text-sm text-surface-400">
              {{ isOnline ? 'Connected' : 'Offline' }}
            </span>
          </div>
          
          <!-- Refresh Button -->
          <Button
            icon="pi pi-refresh"
            :loading="loading"
            severity="secondary"
            outlined
            @click="refreshData"
            class="p-button-sm"
            v-tooltip.bottom="'Refresh Data'"
          />
          
          <!-- Settings (placeholder) -->
          <Button
            icon="pi pi-cog"
            severity="secondary"
            text
            @click="openSettings"
            class="p-button-sm"
            v-tooltip.bottom="'Settings'"
          />
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useFootballStore } from '@/stores/football'
import apiClient from '@/api'

const router = useRouter()
const route = useRoute()
const toast = useToast()
const footballStore = useFootballStore()

// State
const isOnline = ref(true)
const loading = computed(() => footballStore.loading)

// Methods
const refreshData = async () => {
  try {
    // Check which sport we're on and refresh accordingly
    if (route.meta.sport === 'football') {
      await footballStore.initializeDashboard()
      toast.add({
        severity: 'success',
        summary: 'Data Refreshed',
        detail: 'Football data has been updated',
        life: 3000
      })
    } else {
      // Just check API health for other sports
      await apiClient.health()
      toast.add({
        severity: 'success',
        summary: 'Connection Verified',
        detail: 'API connection is healthy',
        life: 3000
      })
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Refresh Failed',
      detail: 'Unable to refresh data. Please try again.',
      life: 5000
    })
  }
}

const openSettings = () => {
  toast.add({
    severity: 'info',
    summary: 'Settings',
    detail: 'Settings panel coming soon!',
    life: 3000
  })
}

const checkConnectionStatus = async () => {
  try {
    await apiClient.health()
    isOnline.value = true
  } catch (error) {
    isOnline.value = false
  }
}

// Lifecycle
onMounted(() => {
  checkConnectionStatus()
  
  // Check connection status periodically
  setInterval(checkConnectionStatus, 30000) // Every 30 seconds
})
</script>

<style scoped>
/* Additional header-specific styles if needed */
.container {
  max-width: 1200px;
}

/* Logo animation on hover */
.w-10.h-10 {
  transition: transform 0.2s ease;
}

.w-10.h-10:hover {
  transform: scale(1.05);
}
</style>