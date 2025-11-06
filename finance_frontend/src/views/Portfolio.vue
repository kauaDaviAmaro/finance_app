<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type PortfolioSummary, type PortfolioItem, type PortfolioItemCreate, type PortfolioItemUpdate } from '../services/api/index'
import { BarChart, Plus, Trash2, Loader2, AlertCircle, X, DollarSign, TrendingUp, TrendingDown, Calendar, Search } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()

const portfolio = ref<PortfolioSummary | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const creating = ref(false)
const selling = ref<number | null>(null)
const deleting = ref<number | null>(null)
const showAddForm = ref(false)
const showSellForm = ref<number | null>(null)

const newPosition = ref<PortfolioItemCreate>({
  ticker: '',
  quantity: 1,
  purchase_price: 0,
  purchase_date: new Date().toISOString().split('T')[0],
})

const sellData = ref<PortfolioItemUpdate>({
  sold_price: 0,
  sold_date: new Date().toISOString().split('T')[0],
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

async function loadPortfolio() {
  loading.value = true
  error.value = null
  try {
    portfolio.value = await api.getPortfolio()
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

async function addPosition() {
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
    await api.addPortfolioItem(newPosition.value)
    
    // Reset form
    newPosition.value = {
      ticker: '',
      quantity: 1,
      purchase_price: 0,
      purchase_date: new Date().toISOString().split('T')[0],
    }
    showAddForm.value = false
    await loadPortfolio()
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
    sold_date: new Date().toISOString().split('T')[0],
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
    await api.sellPortfolioItem(itemId, sellData.value)
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
    await api.deletePortfolioItem(itemId)
    await loadPortfolio()
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

  await loadPortfolio()
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
              <h1>Meu Portfólio</h1>
              <p class="subtitle">Gerencie suas posições e acompanhe sua performance</p>
            </div>
          </div>
          <button @click="showAddForm = !showAddForm" class="add-button">
            <Plus :size="20" />
            <span>Nova Posição</span>
          </button>
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

      <!-- Add Form -->
      <div v-if="showAddForm" class="add-form-card">
        <div class="form-header">
          <h3>Adicionar Nova Posição</h3>
          <button @click="showAddForm = false" class="close-button">
            <X :size="20" />
          </button>
        </div>
        <div class="form-content">
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

          <div class="form-actions">
            <button @click="addPosition" :disabled="creating || !newPosition.ticker.trim()" class="submit-button">
              <Loader2 v-if="creating" :size="16" class="spinner" />
              <span>{{ creating ? 'Adicionando...' : 'Adicionar Posição' }}</span>
            </button>
            <button @click="showAddForm = false" :disabled="creating" class="cancel-button">
              Cancelar
            </button>
          </div>
        </div>
      </div>

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

      <!-- Empty State -->
      <div v-else-if="!portfolio || portfolio.positions.length === 0" class="empty-state">
        <BarChart :size="64" class="empty-icon" />
        <h2>Seu portfólio está vazio</h2>
        <p>Adicione suas primeiras posições para começar a acompanhar seus investimentos</p>
        <button @click="showAddForm = true" class="empty-action-button">
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
  </div>
</template>

<style scoped>
.portfolio-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
}

.portfolio-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
}

.header-section {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
}

.title-icon {
  color: white;
}

.title-group h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: white;
}

.subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
  color: rgba(255, 255, 255, 0.95);
}

.add-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: white;
  color: #3b82f6;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.add-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-header h3 {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  margin: 0;
}

.stat-icon {
  color: #3b82f6;
}

.stat-icon.positive {
  color: #10b981;
}

.stat-icon.negative {
  color: #ef4444;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.negative {
  color: #ef4444;
}

.stat-percentage {
  font-size: 14px;
  font-weight: 600;
  margin: 4px 0 0 0;
}

.stat-percentage.positive {
  color: #10b981;
}

.stat-percentage.negative {
  color: #ef4444;
}

/* Add Form */
.add-form-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.form-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-button:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  color: #64748b;
  pointer-events: none;
}

.input-wrapper input,
.input-group input,
.input-group select {
  width: 100%;
  padding: 12px 12px 12px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s;
}

.input-group input[type="number"],
.input-group input[type="date"] {
  padding-left: 12px;
}

.input-wrapper input:focus,
.input-group input:focus,
.input-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-wrapper input:disabled,
.input-group input:disabled,
.input-group select:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.submit-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  padding: 12px 24px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-button:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}

.cancel-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 12px;
  margin-bottom: 24px;
  border-left: 4px solid #dc2626;
}

.error-banner span {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.error-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  color: #991b1b;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.error-close:hover {
  background: rgba(153, 27, 27, 0.1);
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: white;
  gap: 16px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-container p {
  font-size: 16px;
  opacity: 0.9;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  color: white;
}

.empty-icon {
  margin-bottom: 24px;
  opacity: 0.8;
}

.empty-state h2 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.empty-state p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 32px 0;
  max-width: 400px;
}

.empty-action-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  background: white;
  color: #3b82f6;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.empty-action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* Portfolio Content */
.portfolio-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.positions-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin: 0;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  margin-left: 8px;
}

.positions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.position-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.position-card.active {
  border-left: 4px solid #10b981;
}

.position-card.sold {
  border-left: 4px solid #64748b;
  opacity: 0.9;
}

.position-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.position-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
  gap: 12px;
}

.position-info {
  flex: 1;
}

.position-ticker {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.position-meta {
  font-size: 13px;
  color: #64748b;
  display: block;
}

.position-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.active-badge {
  background: #d1fae5;
  color: #065f46;
}

.sold-badge {
  background: #f1f5f9;
  color: #64748b;
}

.position-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.detail-label {
  color: #64748b;
  font-weight: 500;
}

.detail-value {
  color: #0f172a;
  font-weight: 600;
}

.detail-value.positive {
  color: #10b981;
}

.detail-value.negative {
  color: #ef4444;
}

.position-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-button,
.sell-button {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 10px 16px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover,
.sell-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.delete-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-button:hover:not(:disabled) {
  background: #fecaca;
  transform: scale(1.05);
}

.delete-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Sell Form */
.sell-form {
  margin-top: 20px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
}

.sell-form h4 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.sell-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.sell-form-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 768px) {
  .portfolio-main {
    padding: 40px 16px;
  }

  .title-group h1 {
    font-size: 28px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .add-button {
    width: 100%;
    justify-content: center;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .positions-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .position-actions {
    flex-wrap: wrap;
  }

  .action-button,
  .sell-button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .title-group h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }
}
</style>

