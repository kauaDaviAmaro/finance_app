import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { isTokenValid } from '../utils/jwt'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    requiresPro?: boolean
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
    {
      path: '/scanner',
      name: 'ScannerPro',
      component: () => import('../views/Scanner.vue'),
      meta: { requiresAuth: true, requiresPro: true },
    },
    {
      path: '/subscription',
      name: 'Subscription',
      component: () => import('../views/Subscription.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const token = authStore.token

  // Se a rota requer autenticação, verifica se o token está válido
  if (to.meta.requiresAuth) {
    // Verifica se existe token e se está válido (não expirado)
    if (!token || !isTokenValid(token)) {
      // Se o token estiver inválido ou expirado, remove-o e redireciona para login
      if (token) {
        authStore.logout()
      }
      next('/login')
      return
    }
    
    // Token válido, verifica se está autenticado
    if (!authStore.isAuthenticated) {
      next('/login')
      return
    }
  }

  // Se a rota requer PRO, valida papel do usuário
  if (to.meta.requiresPro) {
    const role = authStore.user?.role
    const isPro = role === 'PRO' || role === 'ADMIN'
    if (!isPro) {
      next('/subscription')
      return
    }
  }

  // Se a rota requer que o usuário não esteja autenticado
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/home')
    return
  }

  // Redireciona para home se estiver na landing page e autenticado
  if (to.path === '/' && authStore.isAuthenticated) {
    next('/home')
    return
  }

  next()
})

export default router
