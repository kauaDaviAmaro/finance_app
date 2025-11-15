<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminStats, type AdminStats } from '../../services/api/admin.api'
import { Users, Bell, Briefcase, Eye, TrendingUp, BarChart3, Activity, HelpCircle, X, ExternalLink, Plus } from 'lucide-vue-next'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const stats = ref<AdminStats | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const activeModal = ref<string | null>(null)

async function loadStats() {
  try {
    loading.value = true
    error.value = null
    stats.value = await getAdminStats()
  } catch (err: any) {
    error.value = err.message || 'Erro ao carregar estatísticas'
  } finally {
    loading.value = false
  }
}

function openModal(modalType: string) {
  activeModal.value = modalType
}

function closeModal() {
  activeModal.value = null
}

function navigateTo(path: string) {
  router.push(path)
  closeModal()
}

function getModalTitle(modalType: string): string {
  const titles: Record<string, string> = {
    users: 'Usuários',
    alerts: 'Alertas',
    portfolio: 'Portfólio',
    watchlist: 'Watchlist',
    tickers: 'Ticker Prices',
    scans: 'Scan Results',
    support: 'Suporte'
  }
  return titles[modalType] || 'Opções'
}

function getModalIcon(modalType: string) {
  const icons: Record<string, any> = {
    users: Users,
    alerts: Bell,
    portfolio: Briefcase,
    watchlist: Eye,
    tickers: TrendingUp,
    scans: BarChart3,
    support: Activity
  }
  return icons[modalType] || Users
}

// Chart data for Users by Role
const usersByRoleChartData = computed(() => {
  if (!stats.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = Object.keys(stats.value.users_by_role)
  const data = Object.values(stats.value.users_by_role)
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#ffffff',
        borderWidth: 2,
      },
    ],
  }
})

// Chart data for Alerts by Type
const alertsByTypeChartData = computed(() => {
  if (!stats.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = Object.keys(stats.value.alerts_by_type)
  const data = Object.values(stats.value.alerts_by_type)

  return {
    labels,
    datasets: [
      {
        label: 'Alertas',
        data,
        backgroundColor: '#f59e0b',
        borderRadius: 8,
      },
    ],
  }
})

// Chart data for System Overview
const systemOverviewChartData = computed(() => {
  if (!stats.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = ['Usuários', 'Alertas', 'Portfólio', 'Watchlist', 'Tickers', 'Scans', 'Suporte']
  const data = [
    stats.value.total_users,
    stats.value.total_alerts,
    stats.value.total_portfolio_items,
    stats.value.total_watchlist_items,
    stats.value.total_ticker_prices,
    stats.value.total_scan_results,
    stats.value.total_support_messages,
  ]

  return {
    labels,
    datasets: [
      {
        label: 'Total',
        data,
        backgroundColor: [
          '#3b82f6',
          '#f59e0b',
          '#10b981',
          '#8b5cf6',
          '#ec4899',
          '#06b6d4',
          '#f59e0b',
        ],
        borderRadius: 8,
      },
    ],
  }
})

// Chart data for User Status
const userStatusChartData = computed(() => {
  if (!stats.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = ['Ativos', 'Inativos', 'PRO', 'Admin']
  const active = stats.value.active_users
  const inactive = stats.value.total_users - stats.value.active_users
  const pro = stats.value.pro_users
  const admin = stats.value.admin_users

  return {
    labels,
    datasets: [
      {
        label: 'Usuários',
        data: [active, inactive, pro, admin],
        backgroundColor: ['#10b981', '#ef4444', '#3b82f6', '#8b5cf6'],
        borderRadius: 8,
      },
    ],
  }
})

// Chart data for Alert Status
const alertStatusChartData = computed(() => {
  if (!stats.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = ['Ativos', 'Inativos']
  const active = stats.value.active_alerts
  const inactive = stats.value.total_alerts - stats.value.active_alerts

  return {
    labels,
    datasets: [
      {
        label: 'Alertas',
        data: [active, inactive],
        backgroundColor: ['#10b981', '#64748b'],
        borderRadius: 8,
      },
    ],
  }
})

// Chart data for Users Over Time
const usersOverTimeChartData = computed(() => {
  if (!stats.value || !stats.value.users_over_time) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const usersOverTime = stats.value.users_over_time
  const dates = Object.keys(usersOverTime).sort()
  const counts = dates.map(date => usersOverTime[date])

  // Formatar datas para exibição (apenas algumas para não poluir)
  const labels = dates.map(date => {
    const d = new Date(date)
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  })

  return {
    labels,
    datasets: [
      {
        label: 'Total de Usuários',
        data: counts,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      },
    ],
  }
})

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
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = ((value / total) * 100).toFixed(1)
          return `${label}: ${value} (${percentage}%)`
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
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      callbacks: {
        label: function (context: any) {
          return `${context.dataset.label || ''}: ${context.parsed.y}`
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
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

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        font: {
          size: 12,
        },
        usePointStyle: true,
        padding: 12,
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 13,
        weight: 'bold' as const,
      },
      bodyFont: {
        size: 12,
      },
      callbacks: {
        label: function (context: any) {
          return `${context.dataset.label || ''}: ${context.parsed.y} usuários`
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        maxTicksLimit: 10,
        font: {
          size: 11,
        },
      },
    },
    y: {
      beginAtZero: true,
      ticks: {
        font: {
          size: 11,
        },
        stepSize: 1,
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
    },
  },
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="admin-dashboard">
    <div class="dashboard-header">
      <h1>Dashboard Administrativo</h1>
      <p class="subtitle">Visão geral do sistema</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner">Carregando...</div>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadStats" class="retry-button">Tentar novamente</button>
    </div>

    <div v-else-if="stats" class="dashboard-content">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card clickable" @click="openModal('users')">
          <div class="stat-icon users">
            <Users :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_users }}</h3>
            <p class="stat-label">Total de Usuários</p>
            <div class="stat-details">
              <span class="detail-item">{{ stats.active_users }} ativos</span>
              <span class="detail-item">{{ stats.pro_users }} PRO</span>
              <span class="detail-item">{{ stats.admin_users }} Admin</span>
            </div>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('alerts')">
          <div class="stat-icon alerts">
            <Bell :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_alerts }}</h3>
            <p class="stat-label">Total de Alertas</p>
            <div class="stat-details">
              <span class="detail-item">{{ stats.active_alerts }} ativos</span>
            </div>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('portfolio')">
          <div class="stat-icon portfolio">
            <Briefcase :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_portfolio_items }}</h3>
            <p class="stat-label">Itens de Portfólio</p>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('watchlist')">
          <div class="stat-icon watchlist">
            <Eye :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_watchlist_items }}</h3>
            <p class="stat-label">Itens de Watchlist</p>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('tickers')">
          <div class="stat-icon tickers">
            <TrendingUp :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_ticker_prices }}</h3>
            <p class="stat-label">Ticker Prices</p>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('scans')">
          <div class="stat-icon scans">
            <BarChart3 :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_scan_results }}</h3>
            <p class="stat-label">Scan Results</p>
          </div>
        </div>

        <div class="stat-card clickable" @click="openModal('support')">
          <div class="stat-icon support">
            <Activity :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_support_messages }}</h3>
            <p class="stat-label">Mensagens de Suporte</p>
            <div class="stat-details">
              <span class="detail-item pending">{{ stats.pending_support_messages }} pendentes</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="charts-grid">
        <!-- Users by Role - Doughnut Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <Users :size="24" />
            <h3 class="chart-title">Usuários por Role</h3>
          </div>
          <div v-if="usersByRoleChartData.labels.length > 0" class="chart-wrapper">
            <Doughnut :data="usersByRoleChartData" :options="doughnutChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>

        <!-- Alerts by Type - Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <Bell :size="24" />
            <h3 class="chart-title">Alertas por Tipo</h3>
          </div>
          <div v-if="alertsByTypeChartData.labels.length > 0" class="chart-wrapper">
            <Bar :data="alertsByTypeChartData" :options="barChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>

        <!-- System Overview - Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <BarChart3 :size="24" />
            <h3 class="chart-title">Visão Geral do Sistema</h3>
          </div>
          <div v-if="systemOverviewChartData.labels.length > 0" class="chart-wrapper">
            <Bar :data="systemOverviewChartData" :options="barChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>

        <!-- User Status - Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <Users :size="24" />
            <h3 class="chart-title">Status dos Usuários</h3>
          </div>
          <div v-if="userStatusChartData.labels.length > 0" class="chart-wrapper">
            <Bar :data="userStatusChartData" :options="barChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>

        <!-- Alert Status - Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <Bell :size="24" />
            <h3 class="chart-title">Status dos Alertas</h3>
          </div>
          <div v-if="alertStatusChartData.labels.length > 0" class="chart-wrapper">
            <Bar :data="alertStatusChartData" :options="barChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>

        <!-- Support Messages Status - Doughnut Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <Activity :size="24" />
            <h3 class="chart-title">Mensagens de Suporte</h3>
          </div>
          <div class="support-chart-content">
            <div class="support-stats">
              <div class="support-stat-item">
                <span class="support-stat-label">Total</span>
                <span class="support-stat-value">{{ stats.total_support_messages }}</span>
              </div>
              <div class="support-stat-item pending">
                <span class="support-stat-label">Pendentes</span>
                <span class="support-stat-value">{{ stats.pending_support_messages }}</span>
              </div>
              <div class="support-stat-item resolved">
                <span class="support-stat-label">Resolvidas</span>
                <span class="support-stat-value">{{ stats.total_support_messages - stats.pending_support_messages }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Users Over Time - Line Chart -->
        <div class="chart-card full-width">
          <div class="chart-header">
            <TrendingUp :size="24" />
            <h3 class="chart-title">Crescimento de Usuários ao Longo do Tempo</h3>
          </div>
          <div v-if="usersOverTimeChartData.labels.length > 0" class="chart-wrapper">
            <Line :data="usersOverTimeChartData" :options="lineChartOptions" />
          </div>
          <div v-else class="empty-chart">
            <p>Nenhum dado disponível</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <div v-if="activeModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">
            <component :is="getModalIcon(activeModal)" :size="24" />
            <span>{{ getModalTitle(activeModal) }}</span>
          </h2>
          <button @click="closeModal" class="modal-close">
            <X :size="24" />
          </button>
        </div>
        <div class="modal-body">
          <div v-if="activeModal === 'users'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/users')">
              <Users :size="20" />
              <div class="option-content">
                <h3>Ver Todos os Usuários</h3>
                <p>Visualizar e gerenciar todos os usuários do sistema</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div class="option-card" @click="navigateTo('/admin/users')">
              <Plus :size="20" />
              <div class="option-content">
                <h3>Criar Novo Usuário</h3>
                <p>Adicionar um novo usuário ao sistema</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total:</span>
                <span class="summary-value">{{ stats.total_users }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Ativos:</span>
                <span class="summary-value">{{ stats.active_users }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">PRO:</span>
                <span class="summary-value">{{ stats.pro_users }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Admin:</span>
                <span class="summary-value">{{ stats.admin_users }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'alerts'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/alerts')">
              <Bell :size="20" />
              <div class="option-content">
                <h3>Ver Todos os Alertas</h3>
                <p>Visualizar e gerenciar todos os alertas configurados</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div class="option-card" @click="navigateTo('/admin/alerts')">
              <Plus :size="20" />
              <div class="option-content">
                <h3>Criar Novo Alerta</h3>
                <p>Configurar um novo alerta para um usuário</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total:</span>
                <span class="summary-value">{{ stats.total_alerts }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Ativos:</span>
                <span class="summary-value">{{ stats.active_alerts }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'portfolio'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/portfolio')">
              <Briefcase :size="20" />
              <div class="option-content">
                <h3>Ver Todos os Itens</h3>
                <p>Visualizar todos os itens de portfólio dos usuários</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total de Itens:</span>
                <span class="summary-value">{{ stats.total_portfolio_items }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'watchlist'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/watchlist')">
              <Eye :size="20" />
              <div class="option-content">
                <h3>Ver Todas as Watchlists</h3>
                <p>Visualizar todos os itens de watchlist dos usuários</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total de Itens:</span>
                <span class="summary-value">{{ stats.total_watchlist_items }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'tickers'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/ticker-prices')">
              <TrendingUp :size="20" />
              <div class="option-content">
                <h3>Ver Todos os Preços</h3>
                <p>Visualizar e gerenciar preços de tickers</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div class="option-card" @click="navigateTo('/admin/ticker-prices')">
              <Plus :size="20" />
              <div class="option-content">
                <h3>Adicionar Novo Ticker</h3>
                <p>Adicionar ou atualizar preço de um ticker</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total de Tickers:</span>
                <span class="summary-value">{{ stats.total_ticker_prices }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'scans'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/scan-results')">
              <BarChart3 :size="20" />
              <div class="option-content">
                <h3>Ver Todos os Resultados</h3>
                <p>Visualizar todos os resultados de scan diário</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total de Resultados:</span>
                <span class="summary-value">{{ stats.total_scan_results }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeModal === 'support'" class="modal-options">
            <div class="option-card" @click="navigateTo('/admin/support')">
              <Activity :size="20" />
              <div class="option-content">
                <h3>Ver Todas as Mensagens</h3>
                <p>Visualizar e responder mensagens de suporte</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div class="option-card" @click="navigateTo('/admin/support?status=pending')">
              <Bell :size="20" />
              <div class="option-content">
                <h3>Ver Pendentes</h3>
                <p>Visualizar apenas mensagens pendentes de resposta</p>
              </div>
              <ExternalLink :size="20" />
            </div>
            <div v-if="stats" class="stats-summary">
              <div class="summary-item">
                <span class="summary-label">Total:</span>
                <span class="summary-value">{{ stats.total_support_messages }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Pendentes:</span>
                <span class="summary-value pending">{{ stats.pending_support_messages }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 32px;
}

.dashboard-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 16px;
  color: #64748b;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.spinner {
  font-size: 16px;
  color: #64748b;
}

.error-state p {
  color: #dc2626;
  margin-bottom: 16px;
}

.retry-button {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.users {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.stat-icon.alerts {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stat-icon.portfolio {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stat-icon.watchlist {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
}

.stat-icon.tickers {
  background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
  color: white;
}

.stat-icon.scans {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
}

.stat-icon.support {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.detail-item.pending {
  background: #fef3c7;
  color: #92400e;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 8px 0;
}

.stat-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}

.detail-item {
  font-size: 12px;
  color: #64748b;
  padding: 4px 8px;
  background: #f1f5f9;
  border-radius: 4px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.chart-header svg {
  color: #3b82f6;
}

.chart-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.chart-wrapper {
  height: 300px;
  position: relative;
}

.empty-chart {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
}

.support-chart-content {
  padding: 20px 0;
}

.support-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.support-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.2s;
}

.support-stat-item:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
}

.support-stat-item.pending {
  border-color: #f59e0b;
  background: #fef3c7;
}

.support-stat-item.resolved {
  border-color: #10b981;
  background: #d1fae5;
}

.support-stat-label {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  font-weight: 600;
}

.support-stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
}

.support-stat-item.pending .support-stat-value {
  color: #f59e0b;
}

.support-stat-item.resolved .support-stat-value {
  color: #10b981;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  padding: 24px;
}

.modal-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-card:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateX(4px);
}

.option-card svg:first-child {
  color: #3b82f6;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
}

.option-content h3 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.option-content p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.option-card svg:last-child {
  color: #94a3b8;
  flex-shrink: 0;
}

.stats-summary {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.summary-value.pending {
  color: #f59e0b;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-wrapper {
    height: 250px;
  }

  .support-stats {
    grid-template-columns: 1fr;
  }

  .modal-content {
    max-width: 100%;
    margin: 0;
    border-radius: 16px 16px 0 0;
  }

  .stats-summary {
    grid-template-columns: 1fr;
  }
}
</style>

