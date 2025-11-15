<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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

// Safely get the last technical data point for template usage without TS errors
const lastItem = computed(() => {
  const td = technicalData.value
  if (!td || !td.data || td.data.length === 0) return null
  return td.data[td.data.length - 1]
})

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
            <span class="period-badge">{{ periodOptions.find(p => p.value === technicalData?.period)?.label || period }}</span>
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
                {{ lastItem ? formatCurrency(lastItem.close) : 'N/A' }}
              </div>
            </div>

            <div class="indicator-card">
              <div class="indicator-header">
                <Activity :size="20" />
                <span>RSI (14)</span>
              </div>
              <div class="indicator-value" :style="{ color: getRSIStatus(lastItem?.rsi).color }">
                {{ lastItem?.rsi ? lastItem.rsi.toFixed(2) : 'N/A' }}
              </div>
              <div class="indicator-status">
                {{ getRSIStatus(lastItem?.rsi).status }}
              </div>
            </div>

            <div class="indicator-card">
              <div class="indicator-header">
                <BarChart :size="20" />
                <span>MACD</span>
              </div>
              <div class="indicator-value">
                {{ lastItem?.macd ? lastItem.macd.toFixed(2) : 'N/A' }}
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
@import '../styles/market-analysis.css';
</style>
