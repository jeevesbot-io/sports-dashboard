/**
 * Vue Router configuration for Sports Dashboard.
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: {
        title: 'Sports Dashboard'
      }
    },
    {
      path: '/football',
      name: 'football-dashboard',
      component: () => import('@/views/football/DashboardView.vue'),
      meta: {
        title: 'Football Dashboard',
        sport: 'football'
      }
    },
    {
      path: '/football/teams/:id',
      name: 'football-team-detail',
      component: () => import('@/views/football/TeamDetailView.vue'),
      meta: {
        title: 'Team Detail',
        sport: 'football'
      },
      props: true
    },
    {
      path: '/football/analytics',
      name: 'football-analytics',
      component: () => import('@/views/football/AnalyticsView.vue'),
      meta: {
        title: 'Advanced Analytics',
        sport: 'football'
      }
    },
    {
      path: '/cricket',
      name: 'cricket-dashboard',
      component: () => import('@/views/cricket/DashboardView.vue'),
      meta: {
        title: 'Cricket Dashboard',
        sport: 'cricket',
        comingSoon: true
      }
    },
    {
      path: '/rugby',
      name: 'rugby-dashboard',
      component: () => import('@/views/rugby/DashboardView.vue'),
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