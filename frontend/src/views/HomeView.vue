<template>
  <div class="max-w-[1000px] mx-auto">
    <!-- Hero -->
    <div class="text-center py-12 animate-fade-in">
      <h1 class="font-display">
        <span class="font-light text-5xl text-[var(--sd-text-primary)]">Sports</span><br />
        <span class="font-black text-5xl gradient-text">Dashboard</span>
      </h1>
      <p class="text-[var(--sd-text-muted)] text-lg mt-4 max-w-md mx-auto">
        Analytics & statistics for the sports you love
      </p>
    </div>

    <!-- Sport Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
      <!-- Football -->
      <router-link to="/football" class="group no-underline" style="animation-delay: 100ms">
        <div class="glass-card glass-card-interactive p-8 min-h-[280px] flex flex-col relative overflow-hidden">
          <div class="absolute inset-0 opacity-10 group-hover:opacity-20 transition-opacity" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)"></div>
          <div class="relative z-10 flex-1 flex flex-col">
            <i class="pi pi-futbol text-4xl text-accent-cyan mb-6"></i>
            <h2 class="font-display text-xl font-bold text-[var(--sd-text-primary)] mb-2">Football</h2>
            <p class="text-sm text-[var(--sd-text-muted)] mb-4 flex-1">Premier League standings, form, fixtures & analytics</p>
            <GradientBadge label="ACTIVE" variant="new" />
          </div>
        </div>
      </router-link>

      <!-- Cricket -->
      <div class="opacity-50 cursor-default" style="animation-delay: 200ms">
        <div class="glass-card p-8 min-h-[280px] flex flex-col relative overflow-hidden">
          <div class="absolute inset-0 opacity-10" style="background: linear-gradient(135deg, #f59e0b, #f97316)"></div>
          <div class="relative z-10 flex-1 flex flex-col">
            <i class="pi pi-circle text-4xl text-amber-400 mb-6"></i>
            <h2 class="font-display text-xl font-bold text-[var(--sd-text-primary)] mb-2">Cricket</h2>
            <p class="text-sm text-[var(--sd-text-muted)] mb-4 flex-1">International cricket stats & match analysis</p>
            <GradientBadge label="COMING SOON" variant="soon" />
          </div>
        </div>
      </div>

      <!-- Rugby -->
      <div class="opacity-50 cursor-default" style="animation-delay: 300ms">
        <div class="glass-card p-8 min-h-[280px] flex flex-col relative overflow-hidden">
          <div class="absolute inset-0 opacity-10" style="background: linear-gradient(135deg, #10b981, #14b8a6)"></div>
          <div class="relative z-10 flex-1 flex flex-col">
            <i class="pi pi-circle text-4xl text-emerald-400 mb-6"></i>
            <h2 class="font-display text-xl font-bold text-[var(--sd-text-primary)] mb-2">Rugby</h2>
            <p class="text-sm text-[var(--sd-text-muted)] mb-4 flex-1">International rugby statistics & results</p>
            <GradientBadge label="COMING SOON" variant="soon" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import GradientBadge from '@/components/ui/GradientBadge.vue'
</script>
