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
                {{ activePaperTrade.status === 'ACTIVE' ? 'Ativo' : activePaperTrade.status === 'PAUSED' ? 'Pausado' : 'Parado' }}
              </span>
            </div>
            <div class="actions" :key="`actions-${activePaperTrade.status}-${activePaperTrade.id}`">
              <button 
                v-if="activePaperTrade.status === 'ACTIVE'"
                @click="pausePaperTrading"
                :disabled="pausing"
                class="btn-secondary"
              >
                <Loader2 v-if="pausing" class="spinner" />
                <Pause v-else />
                {{ pausing ? 'Pausando...' : 'Pausar' }}
              </button>
              <button 
                v-else-if="activePaperTrade.status === 'PAUSED'"
                @click="pausePaperTrading"
                :disabled="pausing"
                class="btn-primary"
              >
                <Loader2 v-if="pausing" class="spinner" />
                <Play v-else />
                {{ pausing ? 'Retomando...' : 'Retomar' }}
              </button>
              <button @click="stopPaperTrading" :disabled="pausing" class="btn-danger">
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

          <!-- Gráfico de Evolução do Equity -->
          <div v-if="equityHistory.length > 0" class="chart-section">
            <h3>Evolução do Equity</h3>
            <div class="chart-container">
              <Line :data="equityChartData" :options="equityChartOptions" />
            </div>
          </div>

          <!-- Tabs para Posições e Histórico de Trades -->
          <div class="tabs-section">
            <div class="tabs">
              <button 
                :class="['tab', { active: activeTab === 'open' }]"
                @click="activeTab = 'open'"
              >
                Posições Abertas ({{ positions.length }})
              </button>
              <button 
                :class="['tab', { active: activeTab === 'closed' }]"
                @click="activeTab = 'closed'"
              >
                Trades Fechados ({{ closedPositions.length }})
              </button>
            </div>

            <!-- Posições Abertas -->
            <div v-if="activeTab === 'open'" class="tab-content">
              <div v-if="positions.length > 0" class="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Quantidade</th>
                      <th>Preço Entrada</th>
                      <th>Data Entrada</th>
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
                      <td>{{ formatDateTime(pos.entry_date) }}</td>
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
              <div v-else class="empty-state">
                <Eye class="icon" />
                <p>Nenhuma posição aberta no momento</p>
              </div>
            </div>

            <!-- Trades Fechados -->
            <div v-if="activeTab === 'closed'" class="tab-content">
              <div v-if="closedPositions.length > 0" class="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Quantidade</th>
                      <th>Preço Entrada</th>
                      <th>Preço Saída</th>
                      <th>Data Entrada</th>
                      <th>Data Saída</th>
                      <th>P&L</th>
                      <th>P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="pos in closedPositions" :key="pos.id">
                      <td>{{ pos.ticker }}</td>
                      <td>{{ pos.quantity }}</td>
                      <td>R$ {{ formatCurrency(pos.entry_price) }}</td>
                      <td>R$ {{ formatCurrency(pos.exit_price || 0) }}</td>
                      <td>{{ formatDateTime(pos.entry_date) }}</td>
                      <td>{{ formatDateTime(pos.exit_date) }}</td>
                      <td :class="getPnLClass(pos.pnl || 0)">
                        R$ {{ formatCurrency(pos.pnl || 0) }}
                      </td>
                      <td :class="getPnLClass(pos.pnl || 0)">
                        {{ formatPercent(calculateClosedPnLPercent(pos)) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="empty-state">
                <Clock class="icon" />
                <p>Nenhum trade fechado ainda</p>
              </div>
            </div>
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
            <div 
              v-for="item in history" 
              :key="item.id" 
              class="history-item"
              :class="{ expanded: expandedHistoryId === item.id }"
            >
              <div class="history-item-header" @click="toggleHistoryDetail(item.id)">
                <div class="history-info">
                  <span class="ticker">{{ item.ticker }}</span>
                  <span :class="['status-badge', item.status.toLowerCase()]">
                    {{ item.status }}
                  </span>
                </div>
                <div class="history-metrics">
                  <span>Início: {{ formatDate(item.started_at) }}</span>
                  <span v-if="item.stopped_at">Fim: {{ formatDate(item.stopped_at) }}</span>
                  <span class="capital-info">
                    Capital: R$ {{ formatCurrency(item.current_capital) }}
                  </span>
                </div>
                <button class="expand-btn">
                  <ChevronDown :class="{ rotated: expandedHistoryId === item.id }" />
                </button>
              </div>
              
              <!-- Detalhes Expandidos -->
              <div v-if="expandedHistoryId === item.id" class="history-details">
                <div class="history-detail-metrics">
                  <div class="detail-metric">
                    <span class="detail-label">Capital Inicial</span>
                    <span class="detail-value">R$ {{ formatCurrency(item.initial_capital) }}</span>
                  </div>
                  <div class="detail-metric">
                    <span class="detail-label">Capital Final</span>
                    <span class="detail-value">R$ {{ formatCurrency(item.current_capital) }}</span>
                  </div>
                  <div class="detail-metric">
                    <span class="detail-label">Retorno</span>
                    <span :class="['detail-value', calculateReturn(item) > 0 ? 'positive' : 'negative']">
                      {{ formatPercent(calculateReturn(item)) }}
                    </span>
                  </div>
                  <div class="detail-metric">
                    <span class="detail-label">Total de Trades</span>
                    <span class="detail-value">{{ item.positions?.length || 0 }}</span>
                  </div>
                </div>
                
                <div v-if="item.positions && item.positions.length > 0" class="history-positions">
                  <h4>Trades Realizados</h4>
                  <div class="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Ticker</th>
                          <th>Quantidade</th>
                          <th>Preço Entrada</th>
                          <th>Preço Saída</th>
                          <th>P&L</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="pos in item.positions" :key="pos.id">
                          <td>{{ pos.ticker }}</td>
                          <td>{{ pos.quantity }}</td>
                          <td>R$ {{ formatCurrency(pos.entry_price) }}</td>
                          <td>
                            <span v-if="pos.exit_price">R$ {{ formatCurrency(pos.exit_price) }}</span>
                            <span v-else class="text-muted">-</span>
                          </td>
                          <td :class="getPnLClass(pos.pnl || 0)">
                            <span v-if="pos.pnl !== null && pos.pnl !== undefined">
                              R$ {{ formatCurrency(pos.pnl) }}
                            </span>
                            <span v-else class="text-muted">-</span>
                          </td>
                          <td>
                            <span :class="['status-badge', pos.exit_date ? 'closed' : 'open']">
                              {{ pos.exit_date ? 'Fechado' : 'Aberto' }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { backtestingApi, ApiError } from '../services/api/index'
import type { 
  Strategy, PaperTradeStartRequest, PaperTrade, PaperTradeStatusOut, 
  PaperTradePosition 
} from '../services/api/types'
import { 
  Crown, Play, Pause, Square, Loader2, AlertCircle, X, Eye, Clock, ChevronDown 
} from 'lucide-vue-next'
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
  Filler,
} from 'chart.js'
import Navbar from '../components/Navbar.vue'

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
const isPro = computed(() => authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN')

const strategies = ref<Strategy[]>([])
const activePaperTrade = ref<PaperTrade | null>(null)
const paperTradeStatus = ref<PaperTradeStatusOut | null>(null)
const positions = ref<PaperTradePosition[]>([])
const allPositions = ref<PaperTradePosition[]>([])
const history = ref<PaperTrade[]>([])
const currentPrice = ref<number>(0)
const loading = ref(false)
const historyLoading = ref(false)
const starting = ref(false)
const pausing = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'open' | 'closed'>('open')
const expandedHistoryId = ref<number | null>(null)
const equityHistory = ref<Array<{ date: string; equity: number }>>([])
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
    // Salvar o status atual antes de carregar
    const currentStatus = activePaperTrade.value.status
    
    paperTradeStatus.value = await backtestingApi.getPaperTradingStatus(activePaperTrade.value.ticker)
    positions.value = await backtestingApi.getPaperTradingPositions(activePaperTrade.value.ticker)
    
    // Carregar todas as posições (abertas e fechadas)
    const allPos = await backtestingApi.getPaperTradingAllPositions(activePaperTrade.value.id)
    console.log('Todas as posições carregadas:', allPos.length)
    console.log('Posições com exit_date:', allPos.filter(p => p.exit_date).length)
    allPositions.value = allPos
    
    // Atualizar preço atual (simulado - em produção, buscar do mercado)
    if (positions.value.length > 0) {
      currentPrice.value = positions.value[0].entry_price * 1.02 // Simulação
    }
    
    // Preservar o status atual se ele foi atualizado recentemente
    // (não sobrescrever com o status do paper_trade dentro do status)
    if (paperTradeStatus.value?.paper_trade && activePaperTrade.value) {
      // Atualizar outras propriedades, mas manter o status se ele foi alterado recentemente
      const statusFromResponse = paperTradeStatus.value.paper_trade.status
      // Só atualizar se o status não mudou (para evitar sobrescrever uma mudança recente)
      if (statusFromResponse === currentStatus) {
        activePaperTrade.value = { ...paperTradeStatus.value.paper_trade }
      } else {
        // Atualizar outras propriedades mas manter o status atual
        const updatedTrade = { ...paperTradeStatus.value.paper_trade }
        updatedTrade.status = currentStatus
        activePaperTrade.value = updatedTrade
      }
    }
    
    // Atualizar histórico de equity
    updateEquityHistory()
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
  console.log('pausePaperTrading chamado', { 
    activePaperTrade: activePaperTrade.value, 
    pausing: pausing.value 
  })
  
  if (!activePaperTrade.value || pausing.value) {
    console.log('Retornando early:', { 
      hasActivePaperTrade: !!activePaperTrade.value, 
      isPausing: pausing.value 
    })
    return
  }

  pausing.value = true
  error.value = null
  
  try {
    console.log('Chamando API pausePaperTrading com ID:', activePaperTrade.value.id)
    const updatedTrade = await backtestingApi.pausePaperTrading(activePaperTrade.value.id)
    console.log('Resposta da API:', updatedTrade)
    console.log('Status recebido:', updatedTrade.status)
    
    // Atualizar o status primeiro para garantir que a UI reaja imediatamente
    const newStatus = updatedTrade.status
    
    // Criar um novo objeto para forçar a reatividade do Vue
    const updatedPaperTrade = {
      ...activePaperTrade.value,
      ...updatedTrade,
      status: newStatus
    }
    
    // Substituir o objeto inteiro
    activePaperTrade.value = updatedPaperTrade
    
    console.log('Status após atualização:', activePaperTrade.value.status)
    
    // Se pausou, parar o polling; se retomou, reiniciar
    if (newStatus === 'PAUSED') {
      stopStatusPolling()
    } else if (newStatus === 'ACTIVE') {
      startStatusPolling()
    }
    
    // Aguardar o próximo tick para garantir que o Vue processe a atualização
    await nextTick()
    
    // Recarregar status e posições, mas preservar o status atualizado
    await loadPaperTradingStatus()
    
    // Garantir que o status não foi sobrescrito após o loadPaperTradingStatus
    if (activePaperTrade.value && activePaperTrade.value.status !== newStatus) {
      console.log('Corrigindo status que foi sobrescrito:', activePaperTrade.value.status, '->', newStatus)
      activePaperTrade.value = { ...activePaperTrade.value, status: newStatus }
    }
  } catch (e: any) {
    console.error('Erro ao pausar/retomar paper trading:', e)
    if (e instanceof ApiError) {
      error.value = e.message || 'Erro ao pausar/retomar paper trading'
    } else if (e?.response?.data?.detail) {
      error.value = e.response.data.detail
    } else if (e?.message) {
      error.value = e.message
    } else {
      error.value = 'Erro ao pausar/retomar paper trading'
    }
  } finally {
    pausing.value = false
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
  if (statusInterval) {
    clearInterval(statusInterval)
  }
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

const closedPositions = computed(() => {
  const closed = allPositions.value.filter(pos => {
    // Verificar se a posição foi fechada (tem exit_date)
    const hasExitDate = pos.exit_date !== null && pos.exit_date !== undefined && pos.exit_date !== ''
    return hasExitDate
  })
  return closed
})

const equityChartData = computed(() => {
  if (equityHistory.value.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = equityHistory.value.map(d => new Date(d.date).toLocaleTimeString('pt-BR'))
  const equityValues = equityHistory.value.map(d => d.equity)

  return {
    labels,
    datasets: [
      {
        label: 'Equity',
        data: equityValues,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
      },
    ],
  }
})

const equityChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      padding: 12,
      callbacks: {
        label: function (context: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(context.parsed.y)
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
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        callback: function (value: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(value)
        },
        font: {
          size: 11,
        },
      },
    },
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false,
  },
}

function updateEquityHistory() {
  if (!paperTradeStatus.value || !activePaperTrade.value) return
  
  // Não atualizar histórico se estiver pausado
  if (activePaperTrade.value.status === 'PAUSED') return
  
  const now = new Date().toISOString()
  const equity = paperTradeStatus.value.current_equity
  
  equityHistory.value.push({ date: now, equity })
  
  // Manter apenas os últimos 50 pontos
  if (equityHistory.value.length > 50) {
    equityHistory.value.shift()
  }
}

function calculateClosedPnLPercent(position: PaperTradePosition): number {
  if (!position.exit_price || position.entry_price === 0) return 0
  return ((position.exit_price - position.entry_price) / position.entry_price) * 100
}

function calculateReturn(item: PaperTrade): number {
  if (item.initial_capital === 0) return 0
  return ((item.current_capital - item.initial_capital) / item.initial_capital) * 100
}

async function toggleHistoryDetail(id: number) {
  if (expandedHistoryId.value === id) {
    expandedHistoryId.value = null
  } else {
    expandedHistoryId.value = id
    // Carregar detalhes completos se necessário
    const item = history.value.find(h => h.id === id)
    if (item && (!item.positions || item.positions.length === 0)) {
      try {
        const detail = await backtestingApi.getPaperTradingDetail(id)
        const index = history.value.findIndex(h => h.id === id)
        if (index !== -1) {
          history.value[index] = detail
        }
      } catch (e: any) {
        error.value = e?.message || 'Erro ao carregar detalhes'
      }
    }
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('pt-BR')
}

function formatDateTime(dateString: string | null | undefined) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('pt-BR')
}

async function loadActivePaperTrading() {
  try {
    const activeTrades = await backtestingApi.getActivePaperTrading()
    if (activeTrades.length > 0) {
      // Carregar a primeira simulação ativa ou pausada
      activePaperTrade.value = activeTrades[0]
      await loadPaperTradingStatus()
      
      // Iniciar polling apenas se estiver ativa
      if (activePaperTrade.value.status === 'ACTIVE') {
        startStatusPolling()
      }
    }
  } catch (e: any) {
    // Não mostrar erro se não houver simulações ativas
    if (e.status !== 404) {
      error.value = e?.message || 'Erro ao carregar simulações ativas'
    }
  }
}

onMounted(async () => {
  if (isPro.value) {
    await loadStrategies()
    await loadHistory()
    await loadActivePaperTrading()
  }
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
@import '../styles/paper-trading.css';
</style>

