/**
 * Vue Router configuration for Sports Dashboard.
 */
import { createRouter, createWebHistory } from 'vue-router'

// Import views
import HomeView from '@/views/HomeView.vue'
import FootballDashboardView from '@/views/football/DashboardView.vue'
import FootballTeamDetailView from '@/views/football/TeamDetailView.vue'
import CricketDashboardView from '@/views/cricket/DashboardView.vue'
import RugbyDashboardView from '@/views/rugby/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: 'Sports Dashboard'
      }
    },
    {
      path: '/football',
      name: 'football-dashboard',
      component: FootballDashboardView,
      meta: {
        title: 'Football Dashboard',
        sport: 'football'
      }
    },
    {
      path: '/football/teams/:id',
      name: 'football-team-detail',
      component: FootballTeamDetailView,
      meta: {
        title: 'Team Detail',
        sport: 'football'
      },
      props: true
    },
    {
      path: '/cricket',
      name: 'cricket-dashboard',
      component: CricketDashboardView,
      meta: {
        title: 'Cricket Dashboard',
        sport: 'cricket',
        comingSoon: true
      }
    },
    {
      path: '/rugby',
      name: 'rugby-dashboard',
      component: RugbyDashboardView,
      meta: {
        title: 'Rugby Dashboard',
        sport: 'rugby',
        comingSoon: true
      }
    },
    // Redirect for backwards compatibility
    {
      path: '/dashboard',
      redirect: '/football'
    },
    // 404 fallback
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Update document title
  const title = to.meta?.title as string
  if (title) {
    document.title = `${title} | Sports Dashboard`
  } else {
    document.title = 'Sports Dashboard'
  }
  
  next()
})

export default router