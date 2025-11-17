<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getScannerResults } from '../services/api/scanner.api'
import { api } from '../services/api/index'
import type { ScannerRow, ScannerSort } from '../services/api/types'
import { Crown, Search, Plus, Loader2, Clock, Settings, Zap, Eye, X, BarChart } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()

const isPro = computed(() => {
  return authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN'
})

const results = ref<ScannerRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const addingToWatchlist = ref<string | null>(null)
const removingFromWatchlist = ref<string | null>(null)
const watchlistTickers = ref<Set<string>>(new Set())
const advancedMode = ref(false)

// Modo Simples
const simpleFilter = ref<'oversold' | 'overbought' | 'macd_positive' | 'bb_lower' | null>(null)

// Modo Avançado
const rsiOp = ref<'lt' | 'gt'>('lt')
const rsiVal = ref<number | undefined>(30)
const macdOp = ref<'lt' | 'gt'>('gt')
const macdVal = ref<number | undefined>(0)
const bbTouch = ref<'upper' | 'lower' | 'any' | undefined>(undefined)
const sort = ref<ScannerSort | undefined>('rsi_asc')

function buildParams() {
  const params: Record<string, unknown> = {}
  
  if (advancedMode.value) {
    // Modo Avançado
    if (rsiVal.value !== undefined && rsiVal.value !== null) {
      params[rsiOp.value === 'lt' ? 'rsi_lt' : 'rsi_gt'] = rsiVal.value
    }
    if (macdVal.value !== undefined && macdVal.value !== null) {
      params[macdOp.value === 'gt' ? 'macd_gt' : 'macd_lt'] = macdVal.value
    }
    if (bbTouch.value) params['bb_touch'] = bbTouch.value
    if (sort.value) params['sort'] = sort.value
  } else {
    // Modo Simples
    switch (simpleFilter.value) {
      case 'oversold':
        params['rsi_lt'] = 30
        params['sort'] = 'rsi_asc'
        break
      case 'overbought':
        params['rsi_gt'] = 70
        params['sort'] = 'rsi_desc'
        break
      case 'macd_positive':
        params['macd_gt'] = 0
        params['sort'] = 'macd_desc'
        break
      case 'bb_lower':
        params['bb_touch'] = 'lower'
        params['sort'] = 'rsi_asc'
        break
    }
  }
  
  return params
}

async function fetchResults() {
  if (!isPro.value) return
  
  loading.value = true
  error.value = null
  try {
    const [data] = await Promise.all([
      getScannerResults(buildParams()),
      loadWatchlist() // Recarregar watchlist para verificar status atualizado
    ])
    results.value = data
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar resultados'
  } finally {
    loading.value = false
  }
}

async function loadWatchlist() {
  try {
    const watchlist = await api.getWatchlist()
    watchlistTickers.value = new Set(watchlist.items.map(item => item.ticker))
  } catch (e) {
    // Silenciosamente falha se não conseguir carregar watchlist
    console.error('Erro ao carregar watchlist:', e)
  }
}

async function addToWatchlist(ticker: string) {
  if (watchlistTickers.value.has(ticker)) {
    return // Já está na watchlist
  }
  
  addingToWatchlist.value = ticker
  error.value = null
  try {
    await api.addToWatchlist(ticker)
    watchlistTickers.value.add(ticker)
    // Mostrar feedback de sucesso
    setTimeout(() => {
      addingToWatchlist.value = null
    }, 1000)
  } catch (e: any) {
    error.value = e?.message || 'Erro ao adicionar à watchlist'
    addingToWatchlist.value = null
  }
}

async function removeFromWatchlist(ticker: string) {
  if (!watchlistTickers.value.has(ticker)) {
    return // Não está na watchlist
  }
  
  removingFromWatchlist.value = ticker
  error.value = null
  try {
    await api.removeFromWatchlist(ticker)
    watchlistTickers.value.delete(ticker)
    // Mostrar feedback de sucesso
    setTimeout(() => {
      removingFromWatchlist.value = null
    }, 1000)
  } catch (e: any) {
    error.value = e?.message || 'Erro ao remover da watchlist'
    removingFromWatchlist.value = null
  }
}

function formatNum(n: number | null | undefined) {
  if (n === null || n === undefined) return '-'
  return Number(n).toFixed(2)
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

function goToSubscription() {
  router.push('/subscription')
}

function goToAnalysis(ticker: string) {
  router.push(`/market-analysis?ticker=${ticker}`)
}

onMounted(async () => {
  if (isPro.value) {
    // Não carrega automaticamente - usuário precisa buscar
    await loadWatchlist()
  }
})
</script>

<template>
  <div class="scanner-page">
    <Navbar />
    
    <main class="scanner-main">
      <!-- ESTADO #1: VIRA-LATA (Usuário Free) -->
      <div v-if="!isPro" class="locked-screen">
        <div class="locked-wrapper">
          <div class="locked-icon">
            <Crown :size="64" />
          </div>
          <h1 class="locked-title">Scanner de Oportunidades</h1>
          <p class="locked-text">
            Esta é uma ferramenta <strong>PREMIUM</strong>. Filtre centenas de ações por indicadores técnicos e encontre oportunidades em segundos.
          </p>
          <div class="locked-features">
            <div class="locked-feature">
              <span class="check">✓</span>
              <span>Filtros por RSI, MACD e Bollinger Bands</span>
            </div>
            <div class="locked-feature">
              <span class="check">✓</span>
              <span>Resultados pré-calculados (ultra-rápido)</span>
            </div>
            <div class="locked-feature">
              <span class="check">✓</span>
              <span>Adicione oportunidades direto à watchlist</span>
            </div>
          </div>
          <button @click="goToSubscription" class="upgrade-btn">
            <Crown :size="20" />
            <span>Upgrade para PRO - R$ 19,90/mês</span>
          </button>
        </div>
      </div>

      <!-- ESTADO #2 e #3: PREMIUM -->
      <div v-else class="scanner-wrapper">
        <div class="scanner-header">
          <h1 class="page-title">Scanner de Oportunidades</h1>
          <div class="update-info">
            <Clock :size="16" />
            <span>Resultados pré-calculados às 21:00</span>
          </div>
        </div>

        <!-- Toggle Modo -->
        <div class="mode-switcher">
          <button 
            @click="advancedMode = false" 
            class="mode-btn"
            :class="{ active: !advancedMode }"
          >
            <Zap :size="18" />
            <span>Modo Simples</span>
          </button>
          <button 
            @click="advancedMode = true" 
            class="mode-btn"
            :class="{ active: advancedMode }"
          >
            <Settings :size="18" />
            <span>Modo Avançado</span>
          </button>
        </div>

        <!-- Modo Simples -->
        <div v-if="!advancedMode" class="simple-filters-box">
          <h3 class="section-title">Escolha uma oportunidade:</h3>
          <div class="simple-grid">
            <button 
              @click="simpleFilter = simpleFilter === 'oversold' ? null : 'oversold'"
              class="simple-card"
              :class="{ selected: simpleFilter === 'oversold' }"
            >
              <div class="card-icon">📉</div>
              <div class="card-text">
                <strong>Ações Sobrevendidas</strong>
                <span>RSI abaixo de 30 (oportunidade de compra)</span>
              </div>
            </button>
            
            <button 
              @click="simpleFilter = simpleFilter === 'overbought' ? null : 'overbought'"
              class="simple-card"
              :class="{ selected: simpleFilter === 'overbought' }"
            >
              <div class="card-icon">📈</div>
              <div class="card-text">
                <strong>Ações Sobrecompradas</strong>
                <span>RSI acima de 70 (possível venda)</span>
              </div>
            </button>
            
            <button 
              @click="simpleFilter = simpleFilter === 'macd_positive' ? null : 'macd_positive'"
              class="simple-card"
              :class="{ selected: simpleFilter === 'macd_positive' }"
            >
              <div class="card-icon">🚀</div>
              <div class="card-text">
                <strong>Momentum Positivo</strong>
                <span>MACD positivo (tendência de alta)</span>
              </div>
            </button>
            
            <button 
              @click="simpleFilter = simpleFilter === 'bb_lower' ? null : 'bb_lower'"
              class="simple-card"
              :class="{ selected: simpleFilter === 'bb_lower' }"
            >
              <div class="card-icon">💎</div>
              <div class="card-text">
                <strong>Preço na Banda Inferior</strong>
                <span>Toque na Bollinger Band inferior (suporte)</span>
              </div>
            </button>
          </div>
          
          <button 
            @click="fetchResults" 
            class="search-btn" 
            :disabled="loading || !simpleFilter"
          >
            <Search :size="20" />
            <span>{{ loading ? 'Buscando...' : 'BUSCAR AGORA' }}</span>
            <Loader2 v-if="loading" :size="20" class="spin" />
          </button>
        </div>

        <!-- Modo Avançado -->
        <div v-else class="advanced-filters-box">
          <div class="filter-item">
            <label class="filter-label">Análise Técnica</label>
            <div class="filter-controls">
              <select v-model="rsiOp" class="filter-select-op">
                <option value="lt">Menor que (&lt;)</option>
                <option value="gt">Maior que (&gt;)</option>
              </select>
              <input 
                v-model.number="rsiVal" 
                type="number" 
                class="filter-input" 
                placeholder="30"
              />
              <span class="filter-hint">RSI (14)</span>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">Médias Móveis</label>
            <div class="filter-controls">
              <select v-model="macdOp" class="filter-select-op">
                <option value="gt">Maior que (&gt;)</option>
                <option value="lt">Menor que (&lt;)</option>
              </select>
              <input 
                v-model.number="macdVal" 
                type="number" 
                step="0.01"
                class="filter-input" 
                placeholder="0"
              />
              <span class="filter-hint">MACD Hist.</span>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">Bollinger Bands</label>
            <select v-model="bbTouch" class="filter-select">
              <option :value="undefined">—</option>
              <option value="upper">Toque superior</option>
              <option value="lower">Toque inferior</option>
              <option value="any">Qualquer toque</option>
            </select>
          </div>

          <div class="filter-item">
            <label class="filter-label">Ordenar</label>
            <select v-model="sort" class="filter-select">
              <option :value="undefined">—</option>
              <option value="rsi_asc">RSI ↑ (menor primeiro)</option>
              <option value="rsi_desc">RSI ↓ (maior primeiro)</option>
              <option value="macd_desc">MACD Hist. ↓ (maior primeiro)</option>
            </select>
          </div>

          <button @click="fetchResults" class="search-btn" :disabled="loading">
            <Search :size="20" />
            <span>{{ loading ? 'Buscando...' : 'BUSCAR AGORA' }}</span>
            <Loader2 v-if="loading" :size="20" class="spin" />
          </button>
        </div>

        <div v-if="error" class="error-box">
          {{ error }}
        </div>

        <!-- ESTADO #3: Tabela de Resultados -->
        <div v-if="results.length > 0" class="results-box">
          <div class="results-header">
            <h2 class="results-count">{{ results.length }} oportunidades encontradas</h2>
          </div>
          <div class="table-container">
            <table class="results-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Preço Atual</th>
                  <th>RSI (14)</th>
                  <th>MACD Hist.</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in results" :key="row.ticker">
                  <td class="ticker-name">
                    <strong>{{ row.ticker }}</strong>
                  </td>
                  <td>{{ formatCurrency(row.last_price) }}</td>
                  <td :class="{ 'rsi-low': row.rsi_14 && row.rsi_14 < 30, 'rsi-high': row.rsi_14 && row.rsi_14 > 70 }">
                    {{ formatNum(row.rsi_14) }}
                  </td>
                  <td :class="{ 'macd-pos': row.macd_h && row.macd_h > 0 }">
                    {{ formatNum(row.macd_h) }}
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        @click="goToAnalysis(row.ticker)" 
                        class="analysis-btn"
                        title="Ver Análise"
                      >
                        <BarChart :size="16" />
                        <span>Ver Análise</span>
                      </button>
                      <button 
                        v-if="!watchlistTickers.has(row.ticker)"
                        @click="addToWatchlist(row.ticker)" 
                        class="add-btn"
                        :disabled="addingToWatchlist === row.ticker"
                        title="Adicionar à Watchlist"
                      >
                        <Plus v-if="addingToWatchlist !== row.ticker" :size="16" />
                        <Loader2 v-else :size="16" class="spin" />
                        <span>{{ addingToWatchlist === row.ticker ? 'Adicionando...' : 'Adicionar à Watchlist' }}</span>
                      </button>
                      <button 
                        v-else
                        @click="removeFromWatchlist(row.ticker)" 
                        class="remove-btn"
                        :disabled="removingFromWatchlist === row.ticker"
                        title="Remover da Watchlist"
                      >
                        <Eye v-if="removingFromWatchlist !== row.ticker" :size="16" />
                        <Loader2 v-else :size="16" class="spin" />
                        <span>{{ removingFromWatchlist === row.ticker ? 'Removendo...' : 'Remover da Watchlist' }}</span>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else-if="!loading && results.length === 0 && (simpleFilter || advancedMode)" class="empty-box">
          <p>Nenhum resultado encontrado. Ajuste os filtros e tente novamente.</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/scanner.css';
</style>
