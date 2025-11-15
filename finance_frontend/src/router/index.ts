import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { isTokenValid } from '../utils/jwt'
import { useSEO } from '../utils/seo'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    requiresPro?: boolean
    requiresAdmin?: boolean
    layout?: string
    title?: string
    description?: string
    keywords?: string
    noindex?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Landing',
      component: () => import('../views/Landing.vue'),
      meta: {
        title: 'Finance App - Gerencie seus investimentos',
        description: 'Plataforma profissional para traders: scanner de ações, análise técnica com 6+ indicadores, alertas automáticos e gestão de portfólio com P&L em tempo real.',
        keywords: 'investimentos, ações, análise técnica, scanner de ações, RSI, MACD, Bollinger Bands, portfólio, trading, Brasil',
      },
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: {
        requiresGuest: true,
        title: 'Login - Finance App',
        description: 'Faça login na sua conta Finance App para acessar análise técnica, portfólio e watchlist.',
        noindex: true,
      },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/Register.vue'),
      meta: {
        requiresGuest: true,
        title: 'Criar Conta - Finance App',
        description: 'Crie sua conta gratuita no Finance App e comece a gerenciar seus investimentos com análise técnica profissional.',
      },
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('../views/Home.vue'),
      meta: {
        requiresAuth: true,
        title: 'Início - Finance App',
        description: 'Dashboard principal com visão geral dos seus investimentos e análises.',
        noindex: true,
      },
    },
    {
      path: '/market-analysis',
      name: 'MarketAnalysis',
      component: () => import('../views/MarketAnalysis.vue'),
      meta: {
        requiresAuth: true,
        title: 'Análise de Mercado - Finance App',
        description: 'Análise técnica completa com RSI, MACD, Stochastic, Bollinger Bands, ATR e OBV. Gráficos interativos com dados históricos.',
        noindex: true,
      },
    },
    {
      path: '/watchlist',
      name: 'Watchlist',
      component: () => import('../views/Watchlist.vue'),
      meta: {
        requiresAuth: true,
        title: 'Watchlist - Finance App',
        description: 'Monitore suas ações favoritas com acesso rápido à análise técnica e fundamentalista.',
        noindex: true,
      },
    },
    {
      path: '/alerts',
      name: 'Alerts',
      component: () => import('../views/Alerts.vue'),
      meta: {
        requiresAuth: true,
        title: 'Alertas - Finance App',
        description: 'Configure alertas automáticos por indicadores técnicos e receba notificações por email.',
        noindex: true,
      },
    },
    {
      path: '/portfolio',
      name: 'Portfolio',
      component: () => import('../views/Portfolio.vue'),
      meta: {
        requiresAuth: true,
        title: 'Portfólio - Finance App',
        description: 'Gerencie seu portfólio com cálculo automático de P&L realizado e não realizado em tempo real.',
        noindex: true,
      },
    },
    {
      path: '/scanner',
      name: 'ScannerPro',
      component: () => import('../views/Scanner.vue'),
      meta: {
        requiresAuth: true,
        requiresPro: true,
        title: 'Scanner de Ações PRO - Finance App',
        description: 'Filtre centenas de ações por indicadores técnicos: RSI, MACD, Bollinger Bands. Encontre oportunidades rapidamente.',
        noindex: true,
      },
    },
    {
      path: '/subscription',
      name: 'Subscription',
      component: () => import('../views/Subscription.vue'),
      meta: {
        requiresAuth: true,
        title: 'Assinatura PRO - Finance App',
        description: 'Upgrade para PRO e desbloqueie o scanner de ações avançado com filtros por indicadores técnicos.',
        noindex: true,
      },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: {
        requiresAuth: true,
        title: 'Perfil - Finance App',
        description: 'Gerencie suas configurações de perfil e preferências.',
        noindex: true,
      },
    },
    {
      path: '/support',
      name: 'Support',
      component: () => import('../views/Support.vue'),
      meta: {
        requiresAuth: true,
        title: 'Suporte - Finance App',
        description: 'Entre em contato com nossa equipe de suporte.',
        noindex: true,
      },
    },
    // Admin Routes
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, layout: 'admin' },
      redirect: '/admin/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'AdminDashboard',
          component: () => import('../views/admin/AdminDashboard.vue'),
          meta: {
            title: 'Dashboard Admin - Finance App',
            description: 'Painel administrativo do Finance App',
            noindex: true,
          },
        },
        {
          path: 'users',
          name: 'AdminUsers',
          component: () => import('../views/admin/AdminUsers.vue'),
          meta: {
            title: 'Usuários - Admin - Finance App',
            description: 'Gerenciamento de usuários',
            noindex: true,
          },
        },
        {
          path: 'alerts',
          name: 'AdminAlerts',
          component: () => import('../views/admin/AdminAlerts.vue'),
          meta: {
            title: 'Alertas - Admin - Finance App',
            description: 'Gerenciamento de alertas',
            noindex: true,
          },
        },
        {
          path: 'portfolio',
          name: 'AdminPortfolio',
          component: () => import('../views/admin/AdminPortfolio.vue'),
          meta: {
            title: 'Portfólio - Admin - Finance App',
            description: 'Gerenciamento de portfólios',
            noindex: true,
          },
        },
        {
          path: 'watchlist',
          name: 'AdminWatchlist',
          component: () => import('../views/admin/AdminWatchlist.vue'),
          meta: {
            title: 'Watchlist - Admin - Finance App',
            description: 'Gerenciamento de watchlists',
            noindex: true,
          },
        },
        {
          path: 'ticker-prices',
          name: 'AdminTickerPrices',
          component: () => import('../views/admin/AdminTickerPrices.vue'),
          meta: {
            title: 'Ticker Prices - Admin - Finance App',
            description: 'Gerenciamento de preços de tickers',
            noindex: true,
          },
        },
        {
          path: 'scan-results',
          name: 'AdminScanResults',
          component: () => import('../views/admin/AdminScanResults.vue'),
          meta: {
            title: 'Scan Results - Admin - Finance App',
            description: 'Gerenciamento de resultados de scan',
            noindex: true,
          },
        },
        {
          path: 'support',
          name: 'AdminSupport',
          component: () => import('../views/admin/AdminSupport.vue'),
          meta: {
            title: 'Suporte - Admin - Finance App',
            description: 'Gerenciamento de suporte',
            noindex: true,
          },
        },
      ],
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

  // Se a rota requer ADMIN, valida papel do usuário
  if (to.meta.requiresAdmin) {
    const role = authStore.user?.role
    if (role !== 'ADMIN') {
      next('/home')
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

// Update SEO meta tags on route change
router.afterEach((to) => {
  const baseUrl = globalThis.location.origin
  const fullUrl = `${baseUrl}${to.fullPath}`
  
  const seoConfig = {
    title: to.meta.title || 'Finance App',
    description: to.meta.description || 'Plataforma profissional para traders e investidores',
    keywords: to.meta.keywords || 'investimentos, ações, análise técnica, trading',
    url: fullUrl,
  }

  // Update robots meta tag if route should not be indexed
  if (to.meta.noindex) {
    let robotsMeta = document.querySelector('meta[name="robots"]') as HTMLMetaElement
    if (!robotsMeta) {
      robotsMeta = document.createElement('meta')
      robotsMeta.setAttribute('name', 'robots')
      document.head.appendChild(robotsMeta)
    }
    robotsMeta.setAttribute('content', 'noindex, nofollow')
  } else {
    let robotsMeta = document.querySelector('meta[name="robots"]') as HTMLMetaElement
    if (robotsMeta) {
      robotsMeta.setAttribute('content', 'index, follow')
    }
  }

  useSEO(seoConfig)
})

export default router
