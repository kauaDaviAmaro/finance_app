<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, portfolioApi, type PortfolioSummary, type WatchlistResponse, type AlertListResponse, type MostSearchedTicker } from '../services/api/index'
import { DollarSign, TrendingDown, TrendingUp, AlertCircle, Loader2, BarChart, Eye, Bell, Search } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const router = useRouter()
const authStore = useAuthStore()

const portfolio = ref<PortfolioSummary | null>(null)
const watchlist = ref<WatchlistResponse | null>(null)
const alerts = ref<AlertListResponse | null>(null)
const mostSearchedTickers = ref<MostSearchedTicker[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const totalPnL = computed(() => {
  if (!portfolio.value) return 0
  return Number(portfolio.value.total_realized_pnl) + Number(portfolio.value.total_unrealized_pnl)
})

const totalPnLPercentage = computed(() => {
  if (!portfolio.value || Number(portfolio.value.total_invested) === 0) return 0
  return (totalPnL.value / Number(portfolio.value.total_invested)) * 100
})

const recentPositions = computed(() => {
  if (!portfolio.value) return []
  return portfolio.value.positions.slice(0, 5)
})

const recentWatchlist = computed(() => {
  if (!watchlist.value) return []
  return watchlist.value.items.slice(0, 5)
})

const recentAlerts = computed(() => {
  if (!alerts.value) return []
  return alerts.value.alerts.slice(0, 5)
})

// Chart data for P&L Distribution
const pnlChartData = computed(() => {
  if (!portfolio.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const realized = Number(portfolio.value.total_realized_pnl) || 0
  const unrealized = Number(portfolio.value.total_unrealized_pnl) || 0

  const labels = []
  const data = []
  const colors = []

  // Always show realized P&L (positive or negative)
  if (realized !== 0) {
    if (realized > 0) {
      labels.push('P&L Realizado (Positivo)')
      colors.push('#10b981')
    } else {
      labels.push('P&L Realizado (Negativo)')
      colors.push('#ef4444')
    }
    data.push(Math.abs(realized))
  }

  // Always show unrealized P&L (positive or negative)
  if (unrealized !== 0) {
    if (unrealized > 0) {
      labels.push('P&L Não Realizado (Positivo)')
      colors.push('#34d399')
    } else {
      labels.push('P&L Não Realizado (Negativo)')
      colors.push('#f87171')
    }
    data.push(Math.abs(unrealized))
  }

  // If no P&L data, show placeholder
  if (data.length === 0) {
    labels.push('Sem P&L')
    data.push(1)
    colors.push('#94a3b8')
  }

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: colors,
        borderColor: '#ffffff',
        borderWidth: 2,
      },
    ],
  }
})

// Chart data for Portfolio Allocation
const allocationChartData = computed(() => {
  if (!portfolio.value || portfolio.value.positions.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const activePositions = portfolio.value.positions.filter((p) => !p.sold_date)
  if (activePositions.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const allocationMap = new Map<string, number>()
  activePositions.forEach((position) => {
    const invested = Number(position.quantity) * Number(position.purchase_price)
    const current = allocationMap.get(position.ticker) || 0
    allocationMap.set(position.ticker, current + invested)
  })

  const sorted = Array.from(allocationMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  return {
    labels: sorted.map(([ticker]) => ticker),
    datasets: [
      {
        label: 'Valor Investido',
        data: sorted.map(([, value]) => value),
        backgroundColor: '#3b82f6',
        borderRadius: 8,
      },
    ],
  }
})

// Chart data for Top Performers
const performersChartData = computed(() => {
  if (!portfolio.value || portfolio.value.positions.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const activePositions = portfolio.value.positions
    .filter((p) => !p.sold_date && p.unrealized_pnl !== null && p.unrealized_pnl !== undefined)
    .map((p) => ({
      ticker: p.ticker,
      pnl: Number(p.unrealized_pnl),
    }))
    .sort((a, b) => b.pnl - a.pnl)
    .slice(0, 8)

  if (activePositions.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const colors = activePositions.map((p) => (p.pnl >= 0 ? '#10b981' : '#ef4444'))

  return {
    labels: activePositions.map((p) => p.ticker),
    datasets: [
      {
        label: 'P&L Não Realizado',
        data: activePositions.map((p) => p.pnl),
        backgroundColor: colors,
        borderRadius: 8,
      },
    ],
  }
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

function formatPercentage(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

// Chart options
const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        padding: 12,
        usePointStyle: true,
        font: {
          size: 12,
        },
      },
    },
    tooltip: {
      callbacks: {
        label: function (context: any) {
          const label = context.label || ''
          const value = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
          }).format(context.parsed)
          return `${label}: ${value}`
        },
      },
    },
  },
}

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: function (context: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
          }).format(context.parsed.y)
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: function (value: any) {
          if (Math.abs(value) >= 1000000) {
            return `R$ ${(value / 1000000).toFixed(1)}M`
          } else if (Math.abs(value) >= 1000) {
            return `R$ ${(value / 1000).toFixed(1)}k`
          }
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            maximumFractionDigits: 0,
          }).format(value)
        },
        font: {
          size: 11,
        },
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
    },
    x: {
      ticks: {
        font: {
          size: 11,
        },
      },
      grid: {
        display: false,
      },
    },
  },
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    // Buscar portfolios primeiro
    const portfoliosResponse = await portfolioApi.getPortfolios().catch(() => null)
    
    // Se houver portfolios, buscar o primeiro
    let portfolioData = null
    if (portfoliosResponse && portfoliosResponse.portfolios.length > 0) {
      const firstPortfolio = portfoliosResponse.portfolios[0]
      if (firstPortfolio) {
        portfolioData = await portfolioApi.getPortfolio(firstPortfolio.id).catch(() => null)
      }
    }
    
    const [watchlistData, alertsData, mostSearchedData] = await Promise.all([
      api.getWatchlist().catch(() => null),
      api.getAlerts().catch(() => null),
      api.getMostSearchedTickers(10, 7).catch(() => [])
    ])
    
    portfolio.value = portfolioData
    watchlist.value = watchlistData
    alerts.value = alertsData
    mostSearchedTickers.value = mostSearchedData || []
  } catch (err) {
    error.value = 'Erro ao carregar dados. Tente novamente.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function goToTickerAnalysis(ticker: string) {
  router.push(`/market-analysis?ticker=${ticker}`)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  if (!authStore.user) {
    try {
      await authStore.fetchUser()
    } catch {
      router.push('/login')
      return
    }
  }

  await loadData()
})
</script>

<template>
  <div class="home-container">
    <Navbar />

    <main class="home-main">
      <div class="welcome-section">
        <h2>Bem-vindo, {{ authStore.user?.username }}!</h2>
        <p class="subtitle">
          Acompanhe seu portfólio, watchlist e alertas em tempo real.
        </p>
      </div>

      <div v-if="loading" class="loading-container">
        <Loader2 :size="48" class="spinner" />
        <p>Carregando dados...</p>
      </div>

      <div v-else-if="error" class="error-container">
        <AlertCircle :size="48" />
        <p>{{ error }}</p>
        <button @click="loadData" class="retry-button">Tentar novamente</button>
      </div>

      <div v-else class="dashboard-content">
        <!-- Cards de Estatísticas do Portfólio -->
        <div v-if="portfolio" class="stats-grid">
          <div class="stat-card">
            <div class="stat-header">
              <DollarSign :size="24" class="stat-icon" />
              <h3>Total Investido</h3>
            </div>
            <p class="stat-value">{{ formatCurrency(Number(portfolio.total_invested)) }}</p>
          </div>

          <div class="stat-card">
            <div class="stat-header">
              <TrendingUp v-if="totalPnL >= 0" :size="24" class="stat-icon positive" />
              <TrendingDown v-else :size="24" class="stat-icon negative" />
              <h3>Ganhos/Perdas Totais</h3>
            </div>
            <p :class="['stat-value', totalPnL >= 0 ? 'positive' : 'negative']">
              {{ formatCurrency(totalPnL) }}
            </p>
            <p :class="['stat-percentage', totalPnL >= 0 ? 'positive' : 'negative']">
              {{ formatPercentage(totalPnLPercentage) }}
            </p>
          </div>

          <div class="stat-card">
            <div class="stat-header">
              <BarChart :size="24" class="stat-icon" />
              <h3>Posições</h3>
            </div>
            <p class="stat-value">{{ portfolio.positions.length }}</p>
            <p class="stat-subtitle">{{ portfolio.positions.filter(p => !p.sold_date).length }} ativas</p>
          </div>

          <div class="stat-card">
            <div class="stat-header">
              <Eye :size="24" class="stat-icon" />
              <h3>Watchlist</h3>
            </div>
            <p class="stat-value">{{ watchlist?.items.length || 0 }}</p>
            <p class="stat-subtitle">tickers monitorados</p>
          </div>
        </div>

        <!-- Charts Section -->
        <div v-if="portfolio && portfolio.positions && portfolio.positions.length > 0" class="charts-section">
          <!-- P&L Distribution Chart -->
          <div class="chart-card">
            <div class="card-header">
              <BarChart :size="24" />
              <h3>Distribuição de Ganhos/Perdas</h3>
            </div>
            <div v-if="pnlChartData.labels.length > 0 && pnlChartData.datasets.length > 0 && (pnlChartData.datasets[0]?.data?.length ?? 0) > 0" class="chart-wrapper">
              <Doughnut :key="`pnl-${portfolio?.total_realized_pnl || 0}-${portfolio?.total_unrealized_pnl || 0}`" :data="pnlChartData" :options="doughnutChartOptions" />
            </div>
            <div v-else class="empty-state">
              <p>Nenhum dado de P&L disponível</p>
            </div>
          </div>

          <!-- Portfolio Allocation Chart -->
          <div class="chart-card">
            <div class="card-header">
              <BarChart :size="24" />
              <h3>Alocação do Portfólio</h3>
            </div>
            <div v-if="allocationChartData.labels.length > 0" class="chart-wrapper">
              <Bar :key="`allocation-${portfolio?.positions.length || 0}`" :data="allocationChartData" :options="barChartOptions" />
            </div>
            <div v-else class="empty-state">
              <p>Nenhuma posição ativa no portfólio</p>
            </div>
          </div>

          <!-- Top Performers Chart -->
          <div class="chart-card">
            <div class="card-header">
              <TrendingUp :size="24" />
              <h3>Top Performers</h3>
            </div>
            <div v-if="performersChartData.labels.length > 0" class="chart-wrapper">
              <Bar :key="`performers-${portfolio?.positions.length || 0}`" :data="performersChartData" :options="barChartOptions" />
            </div>
            <div v-else class="empty-state">
              <p>Nenhum dado de performance disponível</p>
            </div>
          </div>
        </div>

        <!-- Grid de Conteúdo Principal -->
        <div class="content-grid">
          <!-- Últimas Posições do Portfólio -->
          <div class="content-card">
            <div class="card-header">
              <BarChart :size="24" />
              <h3>Últimas Posições</h3>
            </div>
            <div v-if="recentPositions.length === 0" class="empty-state">
              <p>Nenhuma posição no portfólio ainda.</p>
              <p class="empty-hint">Adicione suas primeiras posições para começar!</p>
            </div>
            <div v-else class="positions-list">
              <div v-for="position in recentPositions" :key="position.id" class="position-item">
                <div class="position-info">
                  <span class="position-ticker">{{ position.ticker }}</span>
                  <span class="position-quantity">{{ position.quantity }} ações</span>
                </div>
                <div class="position-details">
                  <div class="position-price">
                    <span class="label">Compra:</span>
                    <span>{{ formatCurrency(Number(position.purchase_price)) }}</span>
                  </div>
                  <div v-if="position.current_price" class="position-price">
                    <span class="label">Atual:</span>
                    <span>{{ formatCurrency(Number(position.current_price)) }}</span>
                  </div>
                  <div v-if="position.unrealized_pnl !== null && position.unrealized_pnl !== undefined" 
                       :class="['position-pnl', Number(position.unrealized_pnl) >= 0 ? 'positive' : 'negative']">
                    <span class="label">P&L:</span>
                    <span>{{ formatCurrency(Number(position.unrealized_pnl)) }}</span>
                  </div>
                  <div v-if="position.realized_pnl !== null && position.realized_pnl !== undefined" 
                       :class="['position-pnl', Number(position.realized_pnl) >= 0 ? 'positive' : 'negative']">
                    <span class="label">P&L Realizado:</span>
                    <span>{{ formatCurrency(Number(position.realized_pnl)) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Watchlist -->
          <div class="content-card">
            <div class="card-header">
              <Eye :size="24" />
              <h3>Watchlist</h3>
            </div>
            <div v-if="recentWatchlist.length === 0" class="empty-state">
              <p>Nenhum ticker na watchlist ainda.</p>
              <p class="empty-hint">Adicione tickers para monitorar!</p>
            </div>
            <div v-else class="watchlist-list">
              <div v-for="item in recentWatchlist" :key="item.id" class="watchlist-item">
                <span class="watchlist-ticker">{{ item.ticker }}</span>
                <span class="watchlist-date">{{ new Date(item.created_at).toLocaleDateString('pt-BR') }}</span>
              </div>
            </div>
            <div v-if="watchlist && watchlist.items.length > 5" class="card-footer">
              <p>{{ watchlist.items.length - 5 }} mais na lista</p>
            </div>
          </div>

          <!-- Alertas -->
          <div class="content-card">
            <div class="card-header">
              <Bell :size="24" />
              <h3>Alertas</h3>
            </div>
            <div v-if="recentAlerts.length === 0" class="empty-state">
              <p>Nenhum alerta configurado ainda.</p>
              <p class="empty-hint">Configure alertas para monitorar o mercado!</p>
            </div>
            <div v-else class="alerts-list">
              <div v-for="alert in recentAlerts" :key="alert.id" class="alert-item">
                <div class="alert-info">
                  <span class="alert-ticker">{{ alert.ticker }}</span>
                  <span :class="['alert-status', alert.is_active ? 'active' : 'inactive']">
                    {{ alert.is_active ? 'Ativo' : 'Inativo' }}
                  </span>
                </div>
                <div class="alert-details">
                  <span class="alert-indicator">{{ alert.indicator_type }}</span>
                  <span class="alert-condition">{{ alert.condition }}</span>
                  <span v-if="alert.threshold_value" class="alert-threshold">
                    {{ alert.threshold_value }}
                  </span>
                </div>
              </div>
            </div>
            <div v-if="alerts && alerts.alerts.length > 5" class="card-footer">
              <p>{{ alerts.alerts.length - 5 }} mais alertas</p>
            </div>
          </div>
        </div>

        <!-- Tickers Mais Pesquisados -->
        <div class="content-card most-searched-section">
          <div class="card-header">
            <Search :size="24" />
            <h3>Tickers Mais Pesquisados</h3>
          </div>
          <div v-if="mostSearchedTickers.length === 0" class="empty-state">
            <p>Nenhum ticker pesquisado ainda.</p>
            <p class="empty-hint">Os tickers mais pesquisados aparecerão aqui!</p>
          </div>
          <div v-else class="most-searched-list">
            <div 
              v-for="(item, index) in mostSearchedTickers" 
              :key="item.ticker" 
              class="most-searched-item"
              @click="goToTickerAnalysis(item.ticker)"
            >
              <div class="most-searched-rank">{{ index + 1 }}</div>
              <div class="most-searched-info">
                <span class="most-searched-ticker">{{ item.ticker }}</span>
                <span class="most-searched-count">{{ item.search_count }} {{ item.search_count === 1 ? 'pesquisa' : 'pesquisas' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/home.css';
</style>