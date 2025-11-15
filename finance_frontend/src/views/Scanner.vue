<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getScannerResults } from '../services/api/scanner.api'
import { api } from '../services/api/index'
import type { ScannerRow, ScannerSort } from '../services/api/types'
import { Crown, Search, Plus, Loader2, Clock, Settings, Zap } from 'lucide-vue-next'
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
    const data = await getScannerResults(buildParams())
    results.value = data
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar resultados'
  } finally {
    loading.value = false
  }
}

async function addToWatchlist(ticker: string) {
  addingToWatchlist.value = ticker
  error.value = null
  try {
    await api.addToWatchlist(ticker)
  } catch (e: any) {
    error.value = e?.message || 'Erro ao adicionar à watchlist'
  } finally {
    addingToWatchlist.value = null
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

onMounted(() => {
  if (isPro.value) {
    // Não carrega automaticamente - usuário precisa buscar
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
                  <th>BB Lower</th>
                  <th>BB Upper</th>
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
                  <td>{{ formatCurrency(row.bb_lower) }}</td>
                  <td>{{ formatCurrency(row.bb_upper) }}</td>
                  <td>
                    <button 
                      @click="addToWatchlist(row.ticker)" 
                      class="add-btn"
                      :disabled="addingToWatchlist === row.ticker"
                    >
                      <Plus v-if="addingToWatchlist !== row.ticker" :size="16" />
                      <Loader2 v-else :size="16" class="spin" />
                      <span>Adicionar</span>
                    </button>
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
.scanner-page {
  min-height: 100vh;
  background: #f8fafc;
}

.scanner-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* ESTADO #1: LOCKED */
.locked-screen {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  border-radius: 24px;
  padding: 80px 40px;
  text-align: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.locked-screen::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.3;
}

.locked-wrapper {
  position: relative;
  z-index: 1;
  max-width: 600px;
  margin: 0 auto;
}

.locked-icon {
  margin-bottom: 24px;
}

.locked-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.locked-text {
  font-size: 18px;
  line-height: 1.6;
  margin: 0 0 32px 0;
  opacity: 0.95;
}

.locked-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 40px;
  text-align: left;
}

.locked-feature {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}

.check {
  font-weight: 700;
  color: #fbbf24;
  font-size: 20px;
}

.upgrade-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 8px 24px rgba(251, 191, 36, 0.4);
}

.upgrade-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(251, 191, 36, 0.5);
}

/* ESTADO #2 e #3: PREMIUM */
.scanner-wrapper {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.scanner-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e2e8f0;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
}

/* Toggle Modo */
.mode-switcher {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.mode-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: white;
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.mode-btn.active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* Modo Simples */
.simple-filters-box {
  padding: 24px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 20px 0;
}

.simple-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.simple-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.simple-card:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.simple-card.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.card-icon {
  font-size: 32px;
}

.card-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.card-text strong {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
}

.card-text span {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

/* Modo Avançado */
.advanced-filters-box {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  padding: 24px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-bottom: 32px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #475569;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select-op {
  padding: 10px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #0f172a;
  cursor: pointer;
  min-width: 120px;
}

.filter-input {
  padding: 10px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #0f172a;
  flex: 1;
  min-width: 80px;
}

.filter-hint {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
}

.filter-select {
  padding: 10px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #0f172a;
  cursor: pointer;
  width: 100%;
}

.search-btn {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.search-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-box {
  padding: 16px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  margin-bottom: 24px;
  border: 1px solid #fecaca;
}

/* ESTADO #3: Tabela */
.results-box {
  margin-top: 32px;
}

.results-header {
  margin-bottom: 20px;
}

.results-count {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.results-table thead {
  background: #f8fafc;
}

.results-table th {
  padding: 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.results-table td {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
  font-size: 14px;
}

.results-table tbody tr:hover {
  background: #f8fafc;
}

.ticker-name {
  font-weight: 600;
  color: #3b82f6;
}

.rsi-low {
  color: #16a34a;
  font-weight: 600;
}

.rsi-high {
  color: #dc2626;
  font-weight: 600;
}

.macd-pos {
  color: #16a34a;
  font-weight: 600;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f1f5f9;
  color: #3b82f6;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #3b82f6;
  transform: translateY(-1px);
}

.add-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-box {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
  font-size: 16px;
}

@media (max-width: 968px) {
  .simple-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .scanner-main {
    padding: 16px;
  }

  .scanner-wrapper {
    padding: 20px;
  }

  .advanced-filters-box {
    grid-template-columns: 1fr;
  }

  .filter-controls {
    flex-wrap: wrap;
  }

  .simple-grid {
    grid-template-columns: 1fr;
  }

  .results-table {
    font-size: 12px;
  }

  .results-table th,
  .results-table td {
    padding: 12px 8px;
  }
}
</style>
