<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { portfolioApi, riskApi, ApiError, type PortfolioSummary, type PortfolioItem, type PortfolioItemCreate, type PortfolioItemUpdate, type Portfolio, type PortfolioCreate, type PortfolioRiskAnalysis } from '../services/api/index'
import { BarChart, Plus, Trash2, Loader2, AlertCircle, X, DollarSign, TrendingUp, TrendingDown, Search, Edit2, FolderPlus, ChevronDown, Shield, Activity, AlertTriangle, TrendingDown as TrendingDownIcon, ChevronRight } from 'lucide-vue-next'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import Navbar from '../components/Navbar.vue'
import ConfirmDeleteModal from '../components/ConfirmDeleteModal.vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const authStore = useAuthStore()

const portfolios = ref<Portfolio[]>([])
const selectedPortfolioId = ref<number | null>(null)
const portfolio = ref<PortfolioSummary | null>(null)
const loading = ref(true)
const loadingPortfolios = ref(false)
const error = ref<string | null>(null)
const creating = ref(false)
const selling = ref<number | null>(null)
const deleting = ref<number | null>(null)
const deletingPortfolio = ref<number | null>(null)
const showAddForm = ref(false)
const showSellForm = ref<number | null>(null)
const showPortfolioForm = ref(false)
const editingPortfolio = ref<Portfolio | null>(null)
const showPortfolioDropdown = ref(false)
const showDeleteModal = ref(false)
const portfolioToDelete = ref<Portfolio | null>(null)
const riskAnalysis = ref<PortfolioRiskAnalysis | null>(null)
const loadingRisk = ref(false)
const showRiskSection = ref(true)
const expandedPositions = ref<Set<number>>(new Set())

const newPosition = ref<PortfolioItemCreate>({
  portfolio_id: 0,
  ticker: '',
  quantity: 1,
  purchase_price: 0,
  purchase_date: new Date().toISOString().split('T')[0] as string,
})

const newPortfolio = ref<PortfolioCreate>({
  name: '',
  category: null,
  description: null,
})

const sellData = ref<PortfolioItemUpdate>({
  sold_price: 0,
  sold_date: new Date().toISOString().split('T')[0] as string,
})

const totalPnL = computed(() => {
  if (!portfolio.value) return 0
  return Number(portfolio.value.total_realized_pnl) + Number(portfolio.value.total_unrealized_pnl)
})

const totalPnLPercentage = computed(() => {
  if (!portfolio.value || Number(portfolio.value.total_invested) === 0) return 0
  return (totalPnL.value / Number(portfolio.value.total_invested)) * 100
})

const activePositions = computed(() => {
  if (!portfolio.value) return []
  return portfolio.value.positions.filter(p => !p.sold_date)
})

const soldPositions = computed(() => {
  if (!portfolio.value) return []
  return portfolio.value.positions.filter(p => p.sold_date)
})

const selectedPortfolio = computed(() => {
  return portfolios.value.find(p => p.id === selectedPortfolioId.value)
})

const portfolioLimit = computed(() => {
  const role = authStore.user?.role
  if (!role) return 3
  if (role === 'ADMIN') return Infinity
  if (role === 'PRO') return 10
  return 3
})

const canCreatePortfolio = computed(() => {
  return portfolios.value.length < portfolioLimit.value
})

const portfolioCountText = computed(() => {
  if (portfolioLimit.value === Infinity) {
    return `${portfolios.value.length} portfolios`
  }
  return `${portfolios.value.length}/${portfolioLimit.value} portfolios`
})

async function loadPortfolios() {
  loadingPortfolios.value = true
  loading.value = true
  error.value = null
  try {
    const response = await portfolioApi.getPortfolios()
    portfolios.value = response.portfolios
    
    // Selecionar o primeiro portfolio se não houver seleção
    if (portfolios.value.length > 0 && !selectedPortfolioId.value) {
      const firstPortfolio = portfolios.value[0]
      if (firstPortfolio) {
        selectedPortfolioId.value = firstPortfolio.id
        await loadPortfolio()
      }
    } else if (selectedPortfolioId.value) {
      await loadPortfolio()
    } else {
      // Não há portfolios e nenhum selecionado, parar loading
      loading.value = false
      portfolio.value = null
    }
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao carregar portfolios. Tente novamente.'
    }
    console.error(err)
    loading.value = false
  } finally {
    loadingPortfolios.value = false
  }
}

async function loadPortfolio() {
  if (!selectedPortfolioId.value) {
    portfolio.value = null
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = null
  try {
    portfolio.value = await portfolioApi.getPortfolio(selectedPortfolioId.value)
    newPosition.value.portfolio_id = selectedPortfolioId.value
    // Carregar análise de risco se houver posições ativas
    if (activePositions.value.length > 0) {
      await loadRiskAnalysis()
    } else {
      riskAnalysis.value = null
    }
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao carregar portfólio. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function loadRiskAnalysis() {
  if (!selectedPortfolioId.value || activePositions.value.length === 0) {
    return
  }
  
  loadingRisk.value = true
  try {
    riskAnalysis.value = await riskApi.getPortfolioRiskAnalysis(selectedPortfolioId.value)
  } catch (err) {
    console.error('Erro ao carregar análise de risco:', err)
    riskAnalysis.value = null
  } finally {
    loadingRisk.value = false
  }
}

function togglePositionExpansion(index: number) {
  if (expandedPositions.value.has(index)) {
    expandedPositions.value.delete(index)
  } else {
    expandedPositions.value.add(index)
  }
}

// Chart data for drawdown
const drawdownChartData = computed(() => {
  if (!riskAnalysis.value?.metrics.drawdown.drawdown_history.length) {
    return {
      labels: [],
      datasets: []
    }
  }
  
  const history = riskAnalysis.value.metrics.drawdown.drawdown_history
  return {
    labels: history.map(h => {
      const date = new Date(h.date)
      return date.toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' })
    }),
    datasets: [
      {
        label: 'Drawdown (%)',
        data: history.map(h => h.drawdown),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  }
})

const drawdownChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      callbacks: {
        label: (context: any) => `Drawdown: ${context.parsed.y.toFixed(2)}%`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => `${value}%`
      }
    }
  }
}

async function selectPortfolio(portfolioId: number) {
  selectedPortfolioId.value = portfolioId
  showPortfolioDropdown.value = false
  await loadPortfolio()
}

async function addPosition() {
  if (!selectedPortfolioId.value) {
    error.value = 'Por favor, selecione um portfolio'
    return
  }

  if (!newPosition.value.ticker.trim()) {
    error.value = 'Por favor, digite um ticker'
    return
  }

  if (newPosition.value.quantity <= 0) {
    error.value = 'A quantidade deve ser maior que zero'
    return
  }

  if (newPosition.value.purchase_price <= 0) {
    error.value = 'O preço de compra deve ser maior que zero'
    return
  }

  creating.value = true
  error.value = null

  try {
    await portfolioApi.addPortfolioItem(newPosition.value)
    
    // Reset form
    newPosition.value = {
      portfolio_id: selectedPortfolioId.value,
      ticker: '',
      quantity: 1,
      purchase_price: 0,
      purchase_date: new Date().toISOString().split('T')[0] as string,
    }
    showAddForm.value = false
    await loadPortfolio()
    await loadPortfolios() // Atualizar contagem de itens
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao adicionar posição. Tente novamente.'
    }
    console.error(err)
  } finally {
    creating.value = false
  }
}

function openSellForm(item: PortfolioItem) {
  showSellForm.value = item.id
  sellData.value = {
    sold_price: item.current_price || item.purchase_price,
    sold_date: new Date().toISOString().split('T')[0] as string,
  }
}

async function sellPosition(itemId: number) {
  if (sellData.value.sold_price <= 0) {
    error.value = 'O preço de venda deve ser maior que zero'
    return
  }

  selling.value = itemId
  error.value = null

  try {
    await portfolioApi.sellPortfolioItem(itemId, sellData.value)
    showSellForm.value = null
    await loadPortfolio()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao registrar venda. Tente novamente.'
    }
    console.error(err)
  } finally {
    selling.value = null
  }
}

async function deletePosition(itemId: number) {
  const item = portfolio.value?.positions.find(p => p.id === itemId)
  if (!confirm(`Deseja remover a posição de ${item?.ticker}?`)) {
    return
  }

  deleting.value = itemId
  error.value = null

  try {
    await portfolioApi.deletePortfolioItem(itemId)
    await loadPortfolio()
    await loadPortfolios() // Atualizar contagem de itens
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao remover posição. Tente novamente.'
    }
    console.error(err)
  } finally {
    deleting.value = null
  }
}

function openPortfolioForm(portfolio?: Portfolio) {
  editingPortfolio.value = portfolio || null
  if (portfolio) {
    newPortfolio.value = {
      name: portfolio.name,
      category: portfolio.category || null,
      description: portfolio.description || null,
    }
  } else {
    newPortfolio.value = {
      name: '',
      category: null,
      description: null,
    }
  }
  showPortfolioForm.value = true
}

function closePortfolioForm() {
  showPortfolioForm.value = false
  editingPortfolio.value = null
  newPortfolio.value = {
    name: '',
    category: null,
    description: null,
  }
}

async function savePortfolio() {
  if (!newPortfolio.value.name.trim()) {
    error.value = 'Por favor, digite um nome para o portfolio'
    return
  }

  creating.value = true
  error.value = null

  try {
    if (editingPortfolio.value) {
      await portfolioApi.updatePortfolio(editingPortfolio.value.id, newPortfolio.value)
    } else {
      const created = await portfolioApi.createPortfolio(newPortfolio.value)
      selectedPortfolioId.value = created.id
    }
    closePortfolioForm()
    await loadPortfolios()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = editingPortfolio.value 
        ? 'Erro ao atualizar portfolio. Tente novamente.'
        : 'Erro ao criar portfolio. Tente novamente.'
    }
    console.error(err)
  } finally {
    creating.value = false
  }
}

function deletePortfolio(portfolioId: number) {
  const portfolio = portfolios.value.find(p => p.id === portfolioId)
  if (!portfolio) return

  portfolioToDelete.value = portfolio
  showDeleteModal.value = true
}

async function confirmDeletePortfolio() {
  if (!portfolioToDelete.value) return

  const portfolioId = portfolioToDelete.value.id
  deletingPortfolio.value = portfolioId
  error.value = null

  try {
    await portfolioApi.deletePortfolio(portfolioId)
    showDeleteModal.value = false
    portfolioToDelete.value = null
    
    if (selectedPortfolioId.value === portfolioId) {
      selectedPortfolioId.value = null
      portfolio.value = null
    }
    await loadPortfolios()
    if (portfolios.value.length > 0 && !selectedPortfolioId.value) {
      const firstPortfolio = portfolios.value[0]
      if (firstPortfolio) {
        selectedPortfolioId.value = firstPortfolio.id
        await loadPortfolio()
      }
    }
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao deletar portfolio. Tente novamente.'
    }
    console.error(err)
  } finally {
    deletingPortfolio.value = null
  }
}

function cancelDeletePortfolio() {
  showDeleteModal.value = false
  portfolioToDelete.value = null
}

const deleteModalMessage = computed(() => {
  if (!portfolioToDelete.value) return ''
  
  if (portfolioToDelete.value.item_count && portfolioToDelete.value.item_count > 0) {
    return `O portfolio "${portfolioToDelete.value.name}" contém ${portfolioToDelete.value.item_count} posição(ões). Todas as posições serão removidas permanentemente. Deseja continuar?`
  }
  return `Tem certeza que deseja excluir o portfolio "${portfolioToDelete.value.name}"? Esta ação não pode ser desfeita.`
})

const deleteModalWarning = computed(() => {
  if (!portfolioToDelete.value) return ''
  
  if (portfolioToDelete.value.item_count && portfolioToDelete.value.item_count > 0) {
    return `Todas as ${portfolioToDelete.value.item_count} posição(ões) serão removidas permanentemente.`
  }
  return ''
})

function goToAnalysis(ticker: string) {
  router.push(`/market-analysis?ticker=${ticker}`)
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

function formatPercentage(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('pt-BR')
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

  await loadPortfolios()
  document.addEventListener('click', handleClickOutside)
})

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.portfolio-selector-wrapper')) {
    showPortfolioDropdown.value = false
  }
}

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="portfolio-container">
    <Navbar />

    <main class="portfolio-main">
      <div class="header-section">
        <div class="header-content">
          <div class="title-group">
            <BarChart :size="32" class="title-icon" />
            <div>
              <h1>Meus Portfólios</h1>
              <p class="subtitle">Gerencie suas posições e acompanhe sua performance</p>
            </div>
          </div>
          <div class="header-actions">
            <div class="portfolio-selector-wrapper">
              <span class="portfolio-selector-label">Portfolio:</span>
              <div class="portfolio-selector" @click="showPortfolioDropdown = !showPortfolioDropdown">
                <span v-if="selectedPortfolio">{{ selectedPortfolio.name }}</span>
                <span v-else class="placeholder">Selecione um portfolio</span>
                <ChevronDown :size="20" />
              </div>
              
              <div v-if="showPortfolioDropdown" class="portfolio-dropdown">
                <div
                  v-for="p in portfolios"
                  :key="p.id"
                  class="portfolio-dropdown-item"
                  :class="{ active: p.id === selectedPortfolioId }"
                  @click="selectPortfolio(p.id)"
                >
                  <div class="portfolio-dropdown-info">
                    <span class="portfolio-name">{{ p.name }}</span>
                    <span v-if="p.category" class="portfolio-category">{{ p.category }}</span>
                  </div>
                  <span class="portfolio-count">{{ p.item_count || 0 }} itens</span>
                </div>
                <div class="portfolio-dropdown-actions">
                  <button @click="openPortfolioForm()" :disabled="!canCreatePortfolio" class="dropdown-action-button">
                    <FolderPlus :size="16" />
                    <span>Novo Portfolio</span>
                  </button>
                </div>
              </div>
            </div>
            <div class="button-group">
              <div class="button-with-label">
                <span class="button-label">Novo Portfolio:</span>
                <button @click="openPortfolioForm()" :disabled="!canCreatePortfolio" class="add-button secondary">
                  <FolderPlus :size="20" />
                  <span>Novo Portfolio</span>
                </button>
              </div>
              <div class="button-with-label">
                <span class="button-label">Nova Posição:</span>
                <button @click="showAddForm = !showAddForm" :disabled="!selectedPortfolioId" class="add-button">
                  <Plus :size="20" />
                  <span>Nova Posição</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="portfolios.length > 0" class="portfolio-info">
          <span class="portfolio-count-text">{{ portfolioCountText }}</span>
          <div v-if="selectedPortfolio" class="portfolio-actions">
            <button @click="openPortfolioForm(selectedPortfolio)" class="icon-button" title="Editar portfolio">
              <Edit2 :size="16" />
            </button>
            <button 
              @click="deletePortfolio(selectedPortfolio.id)" 
              :disabled="deletingPortfolio === selectedPortfolio.id"
              class="icon-button danger"
              title="Deletar portfolio"
            >
              <Loader2 v-if="deletingPortfolio === selectedPortfolio.id" :size="16" class="spinner" />
              <Trash2 v-else :size="16" />
            </button>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div v-if="portfolio && portfolio.positions.length > 0" class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <DollarSign :size="20" class="stat-icon" />
            <h3>Total Investido</h3>
          </div>
          <p class="stat-value">{{ formatCurrency(Number(portfolio.total_invested)) }}</p>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <TrendingUp v-if="totalPnL >= 0" :size="20" class="stat-icon positive" />
            <TrendingDown v-else :size="20" class="stat-icon negative" />
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
            <BarChart :size="20" class="stat-icon" />
            <h3>Posições Ativas</h3>
          </div>
          <p class="stat-value">{{ activePositions.length }}</p>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <BarChart :size="20" class="stat-icon" />
            <h3>Posições Vendidas</h3>
          </div>
          <p class="stat-value">{{ soldPositions.length }}</p>
        </div>
      </div>

      <!-- Risk Analysis Section -->
      <div v-if="portfolio && activePositions.length > 0" class="risk-section">
        <div class="risk-header">
          <div class="risk-title-group">
            <Shield :size="24" class="risk-icon" />
            <div>
              <h2>Análise de Risco</h2>
              <p class="risk-subtitle">Métricas de risco e gestão do portfólio</p>
            </div>
          </div>
          <button @click="showRiskSection = !showRiskSection" class="toggle-risk-button">
            <ChevronRight :size="20" :class="{ rotated: showRiskSection }" />
          </button>
        </div>

        <div v-if="showRiskSection" class="risk-content">
          <div v-if="loadingRisk" class="risk-loading">
            <Loader2 :size="32" class="spinner" />
            <p>Carregando análise de risco...</p>
          </div>

          <div v-else-if="riskAnalysis" class="risk-metrics">
            <!-- Risk Metrics Cards -->
            <div class="risk-cards-grid">
              <div class="risk-card">
                <div class="risk-card-header">
                  <Activity :size="20" class="risk-card-icon" />
                  <h3>Value at Risk (VaR)</h3>
                </div>
                <div class="risk-card-content">
                  <p v-if="riskAnalysis.metrics.var.var_value" class="risk-value">
                    {{ formatCurrency(riskAnalysis.metrics.var.var_value) }}
                  </p>
                  <p v-else class="risk-value no-data">N/A</p>
                  <p v-if="riskAnalysis.metrics.var.var_percentage" class="risk-percentage">
                    {{ riskAnalysis.metrics.var.var_percentage.toFixed(2) }}%
                  </p>
                  <p class="risk-label">95% confiança, 1 dia</p>
                </div>
              </div>

              <div class="risk-card">
                <div class="risk-card-header">
                  <TrendingDownIcon :size="20" class="risk-card-icon" />
                  <h3>Drawdown Máximo</h3>
                </div>
                <div class="risk-card-content">
                  <p v-if="riskAnalysis.metrics.drawdown.max_drawdown !== null" class="risk-value negative">
                    {{ riskAnalysis.metrics.drawdown.max_drawdown.toFixed(2) }}%
                  </p>
                  <p v-else class="risk-value no-data">N/A</p>
                  <p v-if="riskAnalysis.metrics.drawdown.current_drawdown !== null" class="risk-percentage">
                    Atual: {{ riskAnalysis.metrics.drawdown.current_drawdown.toFixed(2) }}%
                  </p>
                  <p class="risk-label">Maior queda desde o pico</p>
                </div>
              </div>

              <div class="risk-card">
                <div class="risk-card-header">
                  <BarChart :size="20" class="risk-card-icon" />
                  <h3>Beta</h3>
                </div>
                <div class="risk-card-content">
                  <p v-if="riskAnalysis.metrics.beta.portfolio_beta !== null" class="risk-value">
                    {{ riskAnalysis.metrics.beta.portfolio_beta.toFixed(2) }}
                  </p>
                  <p v-else class="risk-value no-data">N/A</p>
                  <p class="risk-label">vs {{ riskAnalysis.metrics.beta.benchmark }}</p>
                </div>
              </div>

              <div class="risk-card">
                <div class="risk-card-header">
                  <Activity :size="20" class="risk-card-icon" />
                  <h3>Volatilidade</h3>
                </div>
                <div class="risk-card-content">
                  <p v-if="riskAnalysis.metrics.volatility.portfolio_volatility !== null" class="risk-value">
                    {{ riskAnalysis.metrics.volatility.portfolio_volatility.toFixed(2) }}%
                  </p>
                  <p v-else class="risk-value no-data">N/A</p>
                  <p class="risk-label">Anualizada</p>
                </div>
              </div>
            </div>

            <!-- Drawdown Chart -->
            <div v-if="drawdownChartData.labels.length > 0" class="risk-chart-card">
              <h3>Histórico de Drawdown</h3>
              <div class="drawdown-chart-container">
                <Line :data="drawdownChartData" :options="drawdownChartOptions" />
              </div>
            </div>

            <!-- Diversification -->
            <div class="diversification-section">
              <h3>Diversificação</h3>
              <div class="diversification-metrics">
                <div class="diversification-metric">
                  <span class="metric-label">Índice de Herfindahl:</span>
                  <span class="metric-value">
                    {{ riskAnalysis.metrics.diversification.herfindahl_index?.toFixed(4) || 'N/A' }}
                  </span>
                </div>
                <div class="diversification-metric">
                  <span class="metric-label">Posições Efetivas:</span>
                  <span class="metric-value">
                    {{ riskAnalysis.metrics.diversification.effective_positions?.toFixed(1) || 'N/A' }}
                  </span>
                </div>
              </div>

              <!-- Warnings -->
              <div v-if="riskAnalysis.metrics.diversification.warnings.length > 0" class="risk-warnings">
                <AlertTriangle :size="20" class="warning-icon" />
                <div class="warnings-list">
                  <p v-for="(warning, idx) in riskAnalysis.metrics.diversification.warnings" :key="idx" class="warning-item">
                    {{ warning }}
                  </p>
                </div>
              </div>

              <!-- Sector Diversification -->
              <div v-if="riskAnalysis.metrics.diversification.sector_diversification.length > 0" class="sector-table">
                <h4>Diversificação por Setor</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Setor</th>
                      <th>Peso</th>
                      <th>Tickers</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(sector, idx) in riskAnalysis.metrics.diversification.sector_diversification" :key="idx">
                      <td>{{ sector.sector }}</td>
                      <td>{{ sector.weight.toFixed(2) }}%</td>
                      <td>{{ sector.tickers.join(', ') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Position Risk Analysis -->
            <div class="position-risk-section">
              <h3>Análise de Risco por Posição</h3>
              <div class="position-risk-list">
                <div
                  v-for="(posAnalysis, idx) in riskAnalysis.position_analyses"
                  :key="idx"
                  class="position-risk-item"
                >
                  <div class="position-risk-header" @click="togglePositionExpansion(idx)">
                    <div class="position-risk-info">
                      <h4>{{ posAnalysis.ticker }}</h4>
                      <span class="position-weight">{{ posAnalysis.portfolio_weight }}% do portfólio</span>
                    </div>
                    <ChevronRight :size="20" :class="{ rotated: expandedPositions.has(idx) }" />
                  </div>
                  
                  <div v-if="expandedPositions.has(idx)" class="position-risk-details">
                    <div class="risk-details-grid">
                      <div class="risk-detail">
                        <span class="detail-label">VaR:</span>
                        <span class="detail-value">
                          {{ posAnalysis.var ? formatCurrency(posAnalysis.var) : 'N/A' }}
                          <span v-if="posAnalysis.var_percentage">({{ posAnalysis.var_percentage.toFixed(2) }}%)</span>
                        </span>
                      </div>
                      <div class="risk-detail">
                        <span class="detail-label">Beta:</span>
                        <span class="detail-value">{{ posAnalysis.beta?.toFixed(2) || 'N/A' }}</span>
                      </div>
                      <div class="risk-detail">
                        <span class="detail-label">Volatilidade:</span>
                        <span class="detail-value">{{ posAnalysis.volatility?.toFixed(2) || 'N/A' }}%</span>
                      </div>
                      <div v-if="posAnalysis.stop_loss" class="risk-detail">
                        <span class="detail-label">Stop Loss:</span>
                        <span class="detail-value negative">
                          {{ formatCurrency(posAnalysis.stop_loss) }}
                          <span v-if="posAnalysis.stop_loss_percentage">({{ posAnalysis.stop_loss_percentage.toFixed(2) }}%)</span>
                        </span>
                      </div>
                      <div v-if="posAnalysis.take_profit" class="risk-detail">
                        <span class="detail-label">Take Profit:</span>
                        <span class="detail-value positive">
                          {{ formatCurrency(posAnalysis.take_profit) }}
                          <span v-if="posAnalysis.take_profit_percentage">({{ posAnalysis.take_profit_percentage.toFixed(2) }}%)</span>
                        </span>
                      </div>
                    </div>
                    
                    <div v-if="posAnalysis.correlations.length > 0" class="correlations">
                      <h5>Correlações</h5>
                      <div class="correlations-list">
                        <span
                          v-for="(corr, corrIdx) in posAnalysis.correlations"
                          :key="corrIdx"
                          class="correlation-tag"
                        >
                          {{ corr.ticker }}: {{ corr.correlation.toFixed(2) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="risk-error">
            <AlertCircle :size="24" />
            <p>Não foi possível carregar a análise de risco</p>
            <button @click="loadRiskAnalysis()" class="retry-button">Tentar novamente</button>
          </div>
        </div>
      </div>

      <!-- Portfolio Form Modal -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="showPortfolioForm" class="modal-overlay" @click="closePortfolioForm">
            <div class="modal-content" @click.stop>
              <div class="modal-header">
                <h2 class="modal-title">{{ editingPortfolio ? 'Editar Portfolio' : 'Novo Portfolio' }}</h2>
                <button @click="closePortfolioForm" class="modal-close" :disabled="creating">
                  <X :size="20" />
                </button>
              </div>
              <div class="modal-body">
                <div class="form-grid">
                  <div class="input-group">
                    <label for="portfolio-name">Nome *</label>
                    <input
                      id="portfolio-name"
                      v-model="newPortfolio.name"
                      type="text"
                      placeholder="Ex: Portfolio Principal"
                      :disabled="creating"
                      required
                    />
                  </div>

                  <div class="input-group">
                    <label for="portfolio-category">Categoria (opcional)</label>
                    <input
                      id="portfolio-category"
                      v-model="newPortfolio.category"
                      type="text"
                      placeholder="Ex: Ações, FIIs, Cripto"
                      :disabled="creating"
                    />
                  </div>

                  <div class="input-group full-width">
                    <label for="portfolio-description">Descrição (opcional)</label>
                    <textarea
                      id="portfolio-description"
                      v-model="newPortfolio.description"
                      placeholder="Descrição do portfolio"
                      :disabled="creating"
                      rows="3"
                    />
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button @click="closePortfolioForm" :disabled="creating" class="cancel-button">
                  Cancelar
                </button>
                <button @click="savePortfolio" :disabled="creating || !newPortfolio.name.trim()" class="submit-button">
                  <Loader2 v-if="creating" :size="16" class="spinner" />
                  <span>{{ creating ? 'Salvando...' : (editingPortfolio ? 'Atualizar' : 'Criar') }}</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Add Position Form Modal -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="showAddForm" class="modal-overlay" @click="showAddForm = false">
            <div class="modal-content" @click.stop>
              <div class="modal-header">
                <h2 class="modal-title">Adicionar Nova Posição</h2>
                <button @click="showAddForm = false" class="modal-close" :disabled="creating">
                  <X :size="20" />
                </button>
              </div>
              <div class="modal-body">
                <div class="form-grid">
                  <div class="input-group">
                    <label for="ticker">Ticker</label>
                    <div class="input-wrapper">
                      <Search :size="20" class="input-icon" />
                      <input
                        id="ticker"
                        v-model="newPosition.ticker"
                        type="text"
                        placeholder="Ex: PETR4, AAPL"
                        :disabled="creating"
                      />
                    </div>
                  </div>

                  <div class="input-group">
                    <label for="quantity">Quantidade</label>
                    <input
                      id="quantity"
                      v-model.number="newPosition.quantity"
                      type="number"
                      min="1"
                      step="1"
                      :disabled="creating"
                    />
                  </div>

                  <div class="input-group">
                    <label for="purchase-price">Preço de Compra (R$)</label>
                    <input
                      id="purchase-price"
                      v-model.number="newPosition.purchase_price"
                      type="number"
                      min="0"
                      step="0.01"
                      :disabled="creating"
                    />
                  </div>

                  <div class="input-group">
                    <label for="purchase-date">Data de Compra</label>
                    <input
                      id="purchase-date"
                      v-model="newPosition.purchase_date"
                      type="date"
                      :disabled="creating"
                    />
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button @click="showAddForm = false" :disabled="creating" class="cancel-button">
                  Cancelar
                </button>
                <button @click="addPosition" :disabled="creating || !newPosition.ticker.trim()" class="submit-button">
                  <Loader2 v-if="creating" :size="16" class="spinner" />
                  <span>{{ creating ? 'Adicionando...' : 'Adicionar Posição' }}</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Error Message -->
      <div v-if="error" class="error-banner">
        <AlertCircle :size="20" />
        <span>{{ error }}</span>
        <button @click="error = null" class="error-close">
          <X :size="16" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <Loader2 :size="48" class="spinner" />
        <p>Carregando portfólio...</p>
      </div>

      <!-- Empty State - No Portfolios -->
      <div v-else-if="portfolios.length === 0" class="empty-state">
        <FolderPlus :size="64" class="empty-icon" />
        <h2>Nenhum portfolio criado</h2>
        <p>Crie seu primeiro portfolio para começar a gerenciar suas posições</p>
        <button @click="openPortfolioForm()" class="empty-action-button">
          <FolderPlus :size="20" />
          <span>Criar Primeiro Portfolio</span>
        </button>
      </div>

      <!-- Empty State - No Positions -->
      <div v-else-if="!portfolio || portfolio.positions.length === 0" class="empty-state">
        <BarChart :size="64" class="empty-icon" />
        <h2>Este portfólio está vazio</h2>
        <p>Adicione suas primeiras posições para começar a acompanhar seus investimentos</p>
        <button @click="showAddForm = true" :disabled="!selectedPortfolioId" class="empty-action-button">
          <Plus :size="20" />
          <span>Adicionar Primeira Posição</span>
        </button>
      </div>

      <!-- Portfolio Content -->
      <div v-else class="portfolio-content">
        <!-- Active Positions -->
        <div v-if="activePositions.length > 0" class="positions-section">
          <h2 class="section-title">
            <TrendingUp :size="24" />
            <span>Posições Ativas</span>
            <span class="badge">{{ activePositions.length }}</span>
          </h2>
          <div class="positions-grid">
            <div
              v-for="position in activePositions"
              :key="position.id"
              class="position-card active"
            >
              <div class="position-header">
                <div class="position-info">
                  <h3 class="position-ticker">{{ position.ticker }}</h3>
                  <span class="position-meta">
                    {{ position.quantity }} ações • Comprado em {{ formatDate(position.purchase_date) }}
                  </span>
                </div>
                <div class="position-badge active-badge">Ativa</div>
              </div>

              <div class="position-details">
                <div class="detail-row">
                  <span class="detail-label">Preço de Compra:</span>
                  <span class="detail-value">{{ formatCurrency(Number(position.purchase_price)) }}</span>
                </div>
                <div v-if="position.current_price" class="detail-row">
                  <span class="detail-label">Preço Atual:</span>
                  <span class="detail-value">{{ formatCurrency(Number(position.current_price)) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Valor Investido:</span>
                  <span class="detail-value">
                    {{ formatCurrency(Number(position.purchase_price) * position.quantity) }}
                  </span>
                </div>
                <div v-if="position.current_price" class="detail-row">
                  <span class="detail-label">Valor Atual:</span>
                  <span class="detail-value">
                    {{ formatCurrency(Number(position.current_price) * position.quantity) }}
                  </span>
                </div>
                <div v-if="position.unrealized_pnl !== null && position.unrealized_pnl !== undefined" 
                     class="detail-row">
                  <span class="detail-label">P&L Não Realizado:</span>
                  <span :class="['detail-value', Number(position.unrealized_pnl) >= 0 ? 'positive' : 'negative']">
                    {{ formatCurrency(Number(position.unrealized_pnl)) }}
                  </span>
                </div>
              </div>

              <div class="position-actions">
                <button @click="goToAnalysis(position.ticker)" class="action-button">
                  <TrendingUp :size="16" />
                  <span>Ver Análise</span>
                </button>
                <button
                  @click="openSellForm(position)"
                  class="sell-button"
                >
                  <DollarSign :size="16" />
                  <span>Vender</span>
                </button>
                <button
                  @click="deletePosition(position.id)"
                  :disabled="deleting === position.id"
                  class="delete-button"
                  title="Remover"
                >
                  <Loader2 v-if="deleting === position.id" :size="16" class="spinner" />
                  <Trash2 v-else :size="18" />
                </button>
              </div>

              <!-- Sell Form -->
              <div v-if="showSellForm === position.id" class="sell-form">
                <h4>Registrar Venda</h4>
                <div class="sell-form-grid">
                  <div class="input-group">
                    <label for="sell-price">Preço de Venda (R$)</label>
                    <input
                      id="sell-price"
                      v-model.number="sellData.sold_price"
                      type="number"
                      min="0"
                      step="0.01"
                      :disabled="selling === position.id"
                    />
                  </div>
                  <div class="input-group">
                    <label for="sell-date">Data de Venda</label>
                    <input
                      id="sell-date"
                      v-model="sellData.sold_date"
                      type="date"
                      :disabled="selling === position.id"
                    />
                  </div>
                </div>
                <div class="sell-form-actions">
                  <button
                    @click="sellPosition(position.id)"
                    :disabled="selling === position.id || sellData.sold_price <= 0"
                    class="submit-button"
                  >
                    <Loader2 v-if="selling === position.id" :size="16" class="spinner" />
                    <span>{{ selling === position.id ? 'Registrando...' : 'Confirmar Venda' }}</span>
                  </button>
                  <button
                    @click="showSellForm = null"
                    :disabled="selling === position.id"
                    class="cancel-button"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sold Positions -->
        <div v-if="soldPositions.length > 0" class="positions-section">
          <h2 class="section-title">
            <BarChart :size="24" />
            <span>Posições Vendidas</span>
            <span class="badge">{{ soldPositions.length }}</span>
          </h2>
          <div class="positions-grid">
            <div
              v-for="position in soldPositions"
              :key="position.id"
              class="position-card sold"
            >
              <div class="position-header">
                <div class="position-info">
                  <h3 class="position-ticker">{{ position.ticker }}</h3>
                  <span class="position-meta">
                    {{ position.quantity }} ações • Vendido em {{ formatDate(position.sold_date!) }}
                  </span>
                </div>
                <div class="position-badge sold-badge">Vendida</div>
              </div>

              <div class="position-details">
                <div class="detail-row">
                  <span class="detail-label">Preço de Compra:</span>
                  <span class="detail-value">{{ formatCurrency(Number(position.purchase_price)) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Preço de Venda:</span>
                  <span class="detail-value">{{ formatCurrency(Number(position.sold_price!)) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Valor Investido:</span>
                  <span class="detail-value">
                    {{ formatCurrency(Number(position.purchase_price) * position.quantity) }}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Valor Vendido:</span>
                  <span class="detail-value">
                    {{ formatCurrency(Number(position.sold_price!) * position.quantity) }}
                  </span>
                </div>
                <div v-if="position.realized_pnl !== null && position.realized_pnl !== undefined" 
                     class="detail-row">
                  <span class="detail-label">P&L Realizado:</span>
                  <span :class="['detail-value', Number(position.realized_pnl) >= 0 ? 'positive' : 'negative']">
                    {{ formatCurrency(Number(position.realized_pnl)) }}
                  </span>
                </div>
              </div>

              <div class="position-actions">
                <button @click="goToAnalysis(position.ticker)" class="action-button">
                  <TrendingUp :size="16" />
                  <span>Ver Análise</span>
                </button>
                <button
                  @click="deletePosition(position.id)"
                  :disabled="deleting === position.id"
                  class="delete-button"
                  title="Remover"
                >
                  <Loader2 v-if="deleting === position.id" :size="16" class="spinner" />
                  <Trash2 v-else :size="18" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Delete Confirmation Modal -->
    <ConfirmDeleteModal
      :show="showDeleteModal"
      title="Confirmar Exclusão"
      :message="deleteModalMessage"
      :warning="deleteModalWarning"
      :loading="deletingPortfolio !== null"
      @confirm="confirmDeletePortfolio"
      @cancel="cancelDeletePortfolio"
    />
  </div>
</template>

<style scoped>
@import '../styles/portfolio.css';
@import '../styles/risk.css';
</style>

