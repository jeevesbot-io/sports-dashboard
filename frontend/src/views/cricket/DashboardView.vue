<template>
  <div class="coming-soon">
    <div class="icon">🏏</div>
    <h1>Cricket</h1>
    <p>International cricket analytics — coming soon.</p>
    <router-link to="/" class="back-link">← Back to Home</router-link>
  </div>
</template>

<style scoped>
.coming-soon {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 500px;
  margin: 0 auto;
}
.icon { font-size: 4rem; margin-bottom: 1rem; }
h1 { color: #f0f0f0; margin: 0 0 0.5rem 0; }
p { color: #888; margin-bottom: 2rem; }
.back-link { color: #888; text-decoration: none; font-size: 0.9rem; }
.back-link:hover { color: #f0f0f0; }
</style>
