<template>
  <div class="paper-trading-page">
    <Navbar />
    <div class="paper-trading-main">
      <div class="paper-trading-header">
        <div class="paper-trading-header-card">
          <div class="paper-trading-header-content">
            <h1>Paper Trading</h1>
            <p class="paper-trading-subtitle">Simule estratégias em tempo real sem risco (PRO)</p>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <AlertCircle class="icon" />
        <span>{{ error }}</span>
        <button @click="error = null" class="close-btn">
          <X />
        </button>
      </div>

      <div v-if="!isPro" class="pro-banner">
        <Crown class="icon" />
        <div class="pro-banner-content">
          <h3>Recurso Exclusivo PRO</h3>
          <p>Upgrade para PRO para acessar paper trading em tempo real</p>
          <button @click="$router.push('/subscription')" class="btn-primary">
            Fazer Upgrade
          </button>
        </div>
      </div>

      <div v-else>
        <!-- Iniciar Paper Trading -->
        <div v-if="!activePaperTrade" class="start-section">
          <h2>Iniciar Nova Simulação</h2>
          <div class="form-card">
            <div class="form-group">
              <label>Estratégia</label>
              <select v-model="startForm.strategy_id" required>
                <option value="">Selecione uma estratégia</option>
                <option v-for="s in strategies" :key="s.id" :value="s.id">
                  {{ s.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Ticker</label>
              <input v-model="startForm.ticker" type="text" placeholder="Ex: PETR4" required />
            </div>
            <div class="form-group">
              <label>Capital Inicial (R$)</label>
              <input v-model.number="startForm.initial_capital" type="number" min="0" step="0.01" />
            </div>
            <button 
              @click="startPaperTrading" 
              :disabled="starting || !startForm.strategy_id"
              class="btn-primary"
            >
              <Loader2 v-if="starting" class="spinner" />
              <Play v-else />
              {{ starting ? 'Iniciando...' : 'Iniciar Simulação' }}
            </button>
          </div>
        </div>

        <!-- Dashboard Ativo -->
        <div v-else class="dashboard">
          <div class="status-header">
            <div>
              <h2>{{ activePaperTrade.ticker }}</h2>
              <span :class="['status-badge', activePaperTrade.status.toLowerCase()]">
                {{ activePaperTrade.status }}
              </span>
            </div>
            <div class="actions">
              <button 
                v-if="activePaperTrade.status === 'ACTIVE'"
                @click="pausePaperTrading"
                class="btn-secondary"
              >
                <Pause />
                Pausar
              </button>
              <button 
                v-else-if="activePaperTrade.status === 'PAUSED'"
                @click="pausePaperTrading"
                class="btn-primary"
              >
                <Play />
                Retomar
              </button>
              <button @click="stopPaperTrading" class="btn-danger">
                <Square />
                Parar
              </button>
            </div>
          </div>

          <!-- Métricas -->
          <div class="metrics-grid">
            <div class="metric-card">
              <span class="metric-label">Capital Inicial</span>
              <span class="metric-value">R$ {{ formatCurrency(activePaperTrade.initial_capital) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Capital Atual</span>
              <span class="metric-value">R$ {{ formatCurrency(paperTradeStatus?.current_equity || activePaperTrade.current_capital) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Retorno Total</span>
              <span :class="['metric-value', paperTradeStatus && paperTradeStatus.total_return > 0 ? 'positive' : 'negative']">
                {{ formatPercent(paperTradeStatus?.total_return) }}
              </span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Posições Abertas</span>
              <span class="metric-value">{{ paperTradeStatus?.open_positions_count || 0 }}</span>
            </div>
          </div>

          <!-- Posições Abertas -->
          <div v-if="positions.length > 0" class="positions-section">
            <h3>Posições Abertas</h3>
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Quantidade</th>
                    <th>Preço Entrada</th>
                    <th>Preço Atual</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pos in positions" :key="pos.id">
                    <td>{{ pos.ticker }}</td>
                    <td>{{ pos.quantity }}</td>
                    <td>R$ {{ formatCurrency(pos.entry_price) }}</td>
                    <td>R$ {{ formatCurrency(currentPrice) }}</td>
                    <td :class="getPnLClass(calculatePnL(pos))">
                      R$ {{ formatCurrency(calculatePnL(pos)) }}
                    </td>
                    <td :class="getPnLClass(calculatePnL(pos))">
                      {{ formatPercent(calculatePnLPercent(pos)) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-else class="empty-state">
            <Eye class="icon" />
            <p>Nenhuma posição aberta no momento</p>
          </div>
        </div>

        <!-- Histórico -->
        <div class="history-section">
          <h2>Histórico de Simulações</h2>
          <div v-if="historyLoading" class="loading">
            <Loader2 class="spinner" />
            <span>Carregando histórico...</span>
          </div>
          <div v-else-if="history.length === 0" class="empty-state">
            <Clock class="icon" />
            <p>Nenhuma simulação anterior</p>
          </div>
          <div v-else class="history-list">
            <div v-for="item in history" :key="item.id" class="history-item">
              <div class="history-info">
                <span class="ticker">{{ item.ticker }}</span>
                <span :class="['status-badge', item.status.toLowerCase()]">
                  {{ item.status }}
                </span>
              </div>
              <div class="history-metrics">
                <span>Início: {{ formatDate(item.started_at) }}</span>
                <span v-if="item.stopped_at">Fim: {{ formatDate(item.stopped_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { backtestingApi, ApiError } from '../services/api/index'
import type { 
  Strategy, PaperTradeStartRequest, PaperTrade, PaperTradeStatusOut, 
  PaperTradePosition 
} from '../services/api/types'
import { 
  Crown, Play, Pause, Square, Loader2, AlertCircle, X, Eye, Clock 
} from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()
const isPro = computed(() => authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN')

const strategies = ref<Strategy[]>([])
const activePaperTrade = ref<PaperTrade | null>(null)
const paperTradeStatus = ref<PaperTradeStatusOut | null>(null)
const positions = ref<PaperTradePosition[]>([])
const history = ref<PaperTrade[]>([])
const currentPrice = ref<number>(0)
const loading = ref(false)
const historyLoading = ref(false)
const starting = ref(false)
const error = ref<string | null>(null)
let statusInterval: number | null = null

const startForm = ref<PaperTradeStartRequest>({
  strategy_id: 0,
  ticker: '',
  initial_capital: 100000,
})

async function loadStrategies() {
  try {
    strategies.value = await backtestingApi.getStrategies()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar estratégias'
  }
}

async function loadPaperTradingStatus() {
  if (!activePaperTrade.value) return

  try {
    paperTradeStatus.value = await backtestingApi.getPaperTradingStatus(activePaperTrade.value.ticker)
    positions.value = await backtestingApi.getPaperTradingPositions(activePaperTrade.value.ticker)
    // Atualizar preço atual (simulado - em produção, buscar do mercado)
    if (positions.value.length > 0) {
      currentPrice.value = positions.value[0].entry_price * 1.02 // Simulação
    }
  } catch (e: any) {
    if (e.status !== 404) {
      error.value = e?.message || 'Erro ao carregar status'
    }
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    history.value = await backtestingApi.getPaperTradingHistory(10)
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar histórico'
  } finally {
    historyLoading.value = false
  }
}

async function startPaperTrading() {
  if (!startForm.value.strategy_id || !startForm.value.ticker) {
    error.value = 'Preencha todos os campos'
    return
  }

  starting.value = true
  error.value = null
  try {
    activePaperTrade.value = await backtestingApi.startPaperTrading(startForm.value)
    await loadPaperTradingStatus()
    startStatusPolling()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao iniciar paper trading'
  } finally {
    starting.value = false
  }
}

async function pausePaperTrading() {
  if (!activePaperTrade.value) return

  try {
    activePaperTrade.value = await backtestingApi.pausePaperTrading(activePaperTrade.value.id)
    await loadPaperTradingStatus()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao pausar/retomar paper trading'
  }
}

async function stopPaperTrading() {
  if (!activePaperTrade.value) return
  if (!confirm('Tem certeza que deseja parar esta simulação?')) return

  try {
    await backtestingApi.stopPaperTrading(activePaperTrade.value.id)
    activePaperTrade.value = null
    paperTradeStatus.value = null
    positions.value = []
    stopStatusPolling()
    await loadHistory()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao parar paper trading'
  }
}

function startStatusPolling() {
  if (statusInterval) return
  statusInterval = window.setInterval(() => {
    if (activePaperTrade.value && activePaperTrade.value.status === 'ACTIVE') {
      loadPaperTradingStatus()
    }
  }, 30000) // Atualizar a cada 30 segundos
}

function stopStatusPolling() {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
}

function calculatePnL(position: PaperTradePosition): number {
  if (!currentPrice.value) return 0
  return (currentPrice.value - position.entry_price) * position.quantity
}

function calculatePnLPercent(position: PaperTradePosition): number {
  if (!currentPrice.value || position.entry_price === 0) return 0
  return ((currentPrice.value - position.entry_price) / position.entry_price) * 100
}

function getPnLClass(pnl: number): string {
  if (pnl > 0) return 'positive'
  if (pnl < 0) return 'negative'
  return ''
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(2)}%`
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('pt-BR')
}

onMounted(async () => {
  if (isPro.value) {
    await loadStrategies()
    await loadHistory()
    // Tentar carregar paper trading ativo
    // (em produção, buscar do backend)
  }
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
@import '../styles/paper-trading.css';
</style>

