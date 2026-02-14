<template>
  <div class="team-detail">
    <router-link to="/football" class="back-link">← Back to League Table</router-link>
    <h1>Team Detail</h1>
    <p class="placeholder">Detailed team statistics coming in Phase 3.</p>
  </div>
</template>

<style scoped>
.team-detail {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1.5rem;
}
.back-link {
  color: #888;
  text-decoration: none;
  font-size: 0.9rem;
}
.back-link:hover { color: #f0f0f0; }
h1 { color: #f0f0f0; margin: 1rem 0; }
.placeholder { color: #666; }
</style>
