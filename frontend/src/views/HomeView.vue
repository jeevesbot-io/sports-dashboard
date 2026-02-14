<template>
  <div class="home-view">
    <div class="hero">
      <h1>⚽ Sports Dashboard</h1>
      <p class="subtitle">Analytics & statistics for the sports you love</p>
    </div>
    <div class="sport-cards">
      <router-link to="/football" class="sport-card football">
        <div class="sport-icon">⚽</div>
        <h2>Football</h2>
        <p>Premier League standings, form, fixtures & analytics</p>
        <span class="badge active">Active</span>
      </router-link>
      <div class="sport-card cricket disabled">
        <div class="sport-icon">🏏</div>
        <h2>Cricket</h2>
        <p>International cricket stats & match analysis</p>
        <span class="badge coming-soon">Coming Soon</span>
      </div>
      <div class="sport-card rugby disabled">
        <div class="sport-icon">🏉</div>
        <h2>Rugby</h2>
        <p>International rugby statistics & results</p>
        <span class="badge coming-soon">Coming Soon</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.hero {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem 0;
}

.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #f0f0f0;
}

.subtitle {
  color: #888;
  font-size: 1.1rem;
}

.sport-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.sport-card {
  background: #1e1e2e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 2rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  position: relative;
}

.sport-card:not(.disabled):hover {
  border-color: #555;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.sport-card.disabled {
  opacity: 0.5;
  cursor: default;
}

.sport-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.sport-card h2 {
  margin: 0 0 0.5rem 0;
  color: #f0f0f0;
}

.sport-card p {
  color: #888;
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.active {
  background: rgba(39, 174, 96, 0.2);
  color: #27ae60;
}

.badge.coming-soon {
  background: rgba(243, 156, 18, 0.2);
  color: #f39c12;
}
</style>
