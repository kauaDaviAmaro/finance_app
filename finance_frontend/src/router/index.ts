import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Landing',
      component: () => import('../views/Landing.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/Register.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('../views/Home.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/market-analysis',
      name: 'MarketAnalysis',
      component: () => import('../views/MarketAnalysis.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/watchlist',
      name: 'Watchlist',
      component: () => import('../views/Watchlist.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/alerts',
      name: 'Alerts',
      component: () => import('../views/Alerts.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolio',
      name: 'Portfolio',
      component: () => import('../views/Portfolio.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/home')
  } else if (to.path === '/' && authStore.isAuthenticated) {
    next('/home')
  } else {
    next()
  }
})

export default router
