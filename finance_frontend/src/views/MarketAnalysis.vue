<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type TechnicalAnalysis, type Fundamentals } from '../services/api/index'
import { TrendingUp, Search, BarChart, Activity, DollarSign, Info } from 'lucide-vue-next'
import PriceChart from '../components/PriceChart.vue'
import VolumeChart from '../components/VolumeChart.vue'
import RSIChart from '../components/RSIChart.vue'
import MACDChart from '../components/MACDChart.vue'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const ticker = ref('')
const period = ref('1y')
const loading = ref(false)
const error = ref('')
const technicalData = ref<TechnicalAnalysis | null>(null)
const fundamentals = ref<Fundamentals | null>(null)
const activeTab = ref<'technical' | 'fundamentals'>('technical')

const periodOptions = [
  { value: '5d', label: '5 Dias' },
  { value: '1mo', label: '1 Mês' },
  { value: '3mo', label: '3 Meses' },
  { value: '6mo', label: '6 Meses' },
  { value: '1y', label: '1 Ano' },
  { value: '2y', label: '2 Anos' },
  { value: '5y', label: '5 Anos' },
  { value: 'max', label: 'Máximo' },
]

async function searchTicker() {
  if (!ticker.value.trim()) {
    error.value = 'Por favor, digite um ticker'
    return
  }

  error.value = ''
  loading.value = true
  technicalData.value = null
  fundamentals.value = null

  try {
    const [techAnalysis, fundData] = await Promise.all([
      api.getTechnicalAnalysis(ticker.value.toUpperCase(), period.value),
      api.getFundamentals(ticker.value.toUpperCase()).catch(() => null),
    ])

    technicalData.value = techAnalysis
    fundamentals.value = fundData
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao buscar dados. Tente novamente.'
    }
  } finally {
    loading.value = false
  }
}

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return 'N/A'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return 'N/A'
  return new Intl.NumberFormat('pt-BR').format(value)
}

function formatPercent(value: number | undefined): string {
  if (value === undefined || value === null) return 'N/A'
  return `${value.toFixed(2)}%`
}

function getRSIStatus(rsi: number | undefined): { status: string; color: string } {
  if (!rsi) return { status: 'N/A', color: '#64748b' }
  if (rsi > 70) return { status: 'Sobrecomprado', color: '#dc2626' }
  if (rsi < 30) return { status: 'Sobrevendido', color: '#16a34a' }
  return { status: 'Neutro', color: '#64748b' }
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

  // Check for ticker in query parameters
  const tickerParam = route.query.ticker as string | undefined
  if (tickerParam) {
    ticker.value = tickerParam.toUpperCase()
    await searchTicker()
  }
})
</script>

<template>
  <div class="analysis-container">
    <Navbar />

    <main class="analysis-main">
      <div class="search-section">
        <div class="search-card">
          <h2>Buscar Ativo</h2>
          <div class="search-form">
            <div class="input-group">
              <label for="ticker">Ticker</label>
              <div class="input-wrapper">
                <Search :size="20" class="input-icon" />
                <input
                  id="ticker"
                  v-model="ticker"
                  type="text"
                  placeholder="Ex: PETR4, AAPL, MSFT"
                  @keyup.enter="searchTicker"
                />
              </div>
            </div>
            <div class="input-group">
              <label for="period">Período</label>
              <select id="period" v-model="period">
                <option v-for="opt in periodOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
            <button @click="searchTicker" :disabled="loading" class="search-button">
              {{ loading ? 'Buscando...' : 'Buscar' }}
            </button>
          </div>
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </div>
      </div>

      <div v-if="technicalData || fundamentals" class="results-section">
        <div class="tabs">
          <button
            @click="activeTab = 'technical'"
            :class="['tab-button', { active: activeTab === 'technical' }]"
          >
            <BarChart :size="18" />
            Análise Técnica
          </button>
          <button
            @click="activeTab = 'fundamentals'"
            :class="['tab-button', { active: activeTab === 'fundamentals' }]"
          >
            <Activity :size="18" />
            Fundamentos
          </button>
        </div>

        <div v-if="activeTab === 'technical' && technicalData" class="technical-tab">
          <div class="ticker-header">
            <h3>{{ technicalData.ticker }}</h3>
            <span class="period-badge">{{ periodOptions.find(p => p.value === technicalData.period)?.label }}</span>
          </div>

          <!-- Gráfico de Preço -->
          <div class="chart-section">
            <h4>Evolução do Preço</h4>
            <div class="chart-card">
              <PriceChart :data="technicalData" />
            </div>
          </div>

          <!-- Indicadores Rápidos -->
          <div class="indicators-grid">
            <div class="indicator-card">
              <div class="indicator-header">
                <TrendingUp :size="20" />
                <span>Preço Atual</span>
              </div>
              <div class="indicator-value">
                {{ technicalData.data.length > 0 ? formatCurrency(technicalData.data[technicalData.data.length - 1].close) : 'N/A' }}
              </div>
            </div>

            <div class="indicator-card">
              <div class="indicator-header">
                <Activity :size="20" />
                <span>RSI (14)</span>
              </div>
              <div class="indicator-value" :style="{ color: getRSIStatus(technicalData.data[technicalData.data.length - 1]?.rsi).color }">
                {{ technicalData.data[technicalData.data.length - 1]?.rsi?.toFixed(2) || 'N/A' }}
              </div>
              <div class="indicator-status">
                {{ getRSIStatus(technicalData.data[technicalData.data.length - 1]?.rsi).status }}
              </div>
            </div>

            <div class="indicator-card">
              <div class="indicator-header">
                <BarChart :size="20" />
                <span>MACD</span>
              </div>
              <div class="indicator-value">
                {{ technicalData.data[technicalData.data.length - 1]?.macd?.toFixed(2) || 'N/A' }}
              </div>
            </div>

            <div class="indicator-card">
              <div class="indicator-header">
                <DollarSign :size="20" />
                <span>Volume Médio</span>
              </div>
              <div class="indicator-value">
                {{ formatNumber(Math.round(technicalData.data.reduce((sum, d) => sum + d.volume, 0) / technicalData.data.length)) }}
              </div>
            </div>
          </div>

          <!-- Gráficos de Indicadores Técnicos -->
          <div class="charts-grid">
            <div class="chart-section">
              <h4>Volume</h4>
              <div class="chart-card">
                <VolumeChart :data="technicalData" />
              </div>
            </div>

            <div class="chart-section">
              <h4>RSI (Relative Strength Index)</h4>
              <div class="chart-card">
                <RSIChart :data="technicalData" />
              </div>
            </div>

            <div class="chart-section">
              <h4>MACD (Moving Average Convergence Divergence)</h4>
              <div class="chart-card">
                <MACDChart :data="technicalData" />
              </div>
            </div>
          </div>

          <div class="data-table-container">
            <h4>Dados Históricos com Indicadores</h4>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Abertura</th>
                    <th>Máxima</th>
                    <th>Mínima</th>
                    <th>Fechamento</th>
                    <th>Volume</th>
                    <th>RSI</th>
                    <th>MACD</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in technicalData.data.slice(-20).reverse()" :key="index">
                    <td>{{ new Date(item.date).toLocaleDateString('pt-BR') }}</td>
                    <td>{{ formatCurrency(item.open) }}</td>
                    <td>{{ formatCurrency(item.high) }}</td>
                    <td>{{ formatCurrency(item.low) }}</td>
                    <td>{{ formatCurrency(item.close) }}</td>
                    <td>{{ formatNumber(item.volume) }}</td>
                    <td :style="{ color: getRSIStatus(item.rsi).color }">
                      {{ item.rsi?.toFixed(2) || 'N/A' }}
                    </td>
                    <td>{{ item.macd?.toFixed(2) || 'N/A' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'fundamentals' && fundamentals" class="fundamentals-tab">
          <div class="ticker-header">
            <h3>{{ fundamentals.ticker }}</h3>
          </div>

          <div class="fundamentals-grid">
            <div class="fundamental-card">
              <div class="fundamental-label">P/L (Price-to-Earnings)</div>
              <div class="fundamental-value">{{ fundamentals.pe_ratio?.toFixed(2) || 'N/A' }}</div>
            </div>

            <div class="fundamental-card">
              <div class="fundamental-label">P/VP (Price-to-Book)</div>
              <div class="fundamental-value">{{ fundamentals.pb_ratio?.toFixed(2) || 'N/A' }}</div>
            </div>

            <div class="fundamental-card">
              <div class="fundamental-label">Dividend Yield</div>
              <div class="fundamental-value">{{ fundamentals.dividend_yield ? formatPercent(fundamentals.dividend_yield) : 'N/A' }}</div>
            </div>

            <div class="fundamental-card">
              <div class="fundamental-label">Beta</div>
              <div class="fundamental-value">{{ fundamentals.beta?.toFixed(2) || 'N/A' }}</div>
              <div class="fundamental-info">
                <Info :size="14" />
                <span>Mede a volatilidade em relação ao mercado</span>
              </div>
            </div>

            <div class="fundamental-card full-width">
              <div class="fundamental-label">Setor</div>
              <div class="fundamental-value">{{ fundamentals.sector || 'N/A' }}</div>
            </div>

            <div class="fundamental-card full-width">
              <div class="fundamental-label">Indústria</div>
              <div class="fundamental-value">{{ fundamentals.industry || 'N/A' }}</div>
            </div>

            <div class="fundamental-card full-width">
              <div class="fundamental-label">Market Cap</div>
              <div class="fundamental-value">
                {{ fundamentals.market_cap ? formatCurrency(fundamentals.market_cap) : 'N/A' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!loading && !error" class="empty-state">
        <TrendingUp :size="64" class="empty-icon" />
        <h3>Busque um ativo para análise</h3>
        <p>Digite o ticker de uma ação e selecione o período para visualizar dados técnicos e fundamentais</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.analysis-container {
  min-height: 100vh;
  background: #f8fafc;
}


.analysis-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
}

.search-section {
  margin-bottom: 32px;
}

.search-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.search-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 24px 0;
}

.search-form {
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 16px;
  align-items: end;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
}

.input-wrapper input,
.input-group select {
  width: 100%;
  padding: 12px 14px 12px 40px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s;
  background: #f8fafc;
  color: #0f172a;
}

.input-group select {
  padding-left: 14px;
}

.input-wrapper input:hover,
.input-group select:hover {
  border-color: #cbd5e1;
  background: white;
}

.input-wrapper input:focus,
.input-group select:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  white-space: nowrap;
}

.search-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.search-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  margin-top: 16px;
  padding: 12px 16px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid #fecaca;
}

.results-section {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 32px;
  border-bottom: 2px solid #e2e8f0;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #64748b;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #3b82f6;
  background: #f8fafc;
}

.tab-button.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.ticker-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.ticker-header h3 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.period-badge {
  padding: 6px 12px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.indicator-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}

.indicator-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
}

.indicator-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.indicator-status {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

.chart-section {
  margin-bottom: 32px;
}

.chart-section h4 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.chart-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  margin-top: 32px;
}

.data-table-container {
  margin-top: 32px;
}

.data-table-container h4 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table thead {
  background: #f8fafc;
}

.data-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
}

.data-table tbody tr:hover {
  background: #f8fafc;
}

.fundamentals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.fundamental-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
}

.fundamental-card.full-width {
  grid-column: 1 / -1;
}

.fundamental-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fundamental-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.fundamental-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 12px;
  color: #64748b;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 24px;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.empty-state p {
  font-size: 16px;
  color: #64748b;
  max-width: 500px;
  margin: 0 auto;
}

@media (max-width: 968px) {
  .search-form {
    grid-template-columns: 1fr;
  }

  .indicators-grid {
    grid-template-columns: 1fr;
  }

  .fundamentals-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .analysis-main {
    padding: 16px;
  }

  .search-card {
    padding: 20px;
  }

  .results-section {
    padding: 20px;
  }

  .table-wrapper {
    overflow-x: scroll;
  }
}
</style>
