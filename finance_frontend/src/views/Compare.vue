<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type TickerComparison } from '../services/api/index'
import { TrendingUp, Search, BarChart, Activity, DollarSign, Loader2, GitCompare } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import { Line, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const authStore = useAuthStore()

const ticker1 = ref('')
const ticker2 = ref('')
const period = ref('1y')
const loading = ref(false)
const error = ref('')
const comparisonData = ref<TickerComparison | null>(null)
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

const lastItem1 = computed(() => {
  if (!comparisonData.value?.ticker1_data?.data || comparisonData.value.ticker1_data.data.length === 0) return null
  return comparisonData.value.ticker1_data.data[comparisonData.value.ticker1_data.data.length - 1]
})

const lastItem2 = computed(() => {
  if (!comparisonData.value?.ticker2_data?.data || comparisonData.value.ticker2_data.data.length === 0) return null
  return comparisonData.value.ticker2_data.data[comparisonData.value.ticker2_data.data.length - 1]
})

async function compareTickers() {
  if (!ticker1.value.trim() || !ticker2.value.trim()) {
    error.value = 'Por favor, digite ambos os tickers'
    return
  }

  if (ticker1.value.trim().toUpperCase() === ticker2.value.trim().toUpperCase()) {
    error.value = 'Os tickers devem ser diferentes'
    return
  }

  error.value = ''
  loading.value = true
  comparisonData.value = null

  try {
    const data = await api.compareTickers(
      ticker1.value.toUpperCase(),
      ticker2.value.toUpperCase(),
      period.value
    )
    comparisonData.value = data
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao comparar tickers. Tente novamente.'
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

function getQualityScoreColor(score: number | undefined): string {
  if (score === undefined || score === null) return '#64748b'
  if (score >= 70) return '#16a34a' // Verde
  if (score >= 50) return '#eab308' // Amarelo
  return '#dc2626' // Vermelho
}

function getQualityScoreLabel(score: number | undefined): string {
  if (score === undefined || score === null) return 'N/A'
  if (score >= 70) return 'Excelente'
  if (score >= 50) return 'Bom'
  return 'Baixo'
}

// Gráficos comparativos
const priceChartData = computed(() => {
  if (!comparisonData.value) return { labels: [], datasets: [] }
  
  const data1 = comparisonData.value.ticker1_data.data
  const data2 = comparisonData.value.ticker2_data.data
  
  const labels = data1.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const prices1 = data1.map((d) => d.close)
  const prices2 = data2.map((d) => d.close)
  
  return {
    labels,
    datasets: [
      {
        label: comparisonData.value.ticker1,
        data: prices1,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: comparisonData.value.ticker2,
        data: prices2,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
    ],
  }
})

const volumeChartData = computed(() => {
  if (!comparisonData.value) return { labels: [], datasets: [] }
  
  const data1 = comparisonData.value.ticker1_data.data
  const data2 = comparisonData.value.ticker2_data.data
  
  const labels = data1.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const volumes1 = data1.map((d) => d.volume)
  const volumes2 = data2.map((d) => d.volume)
  
  return {
    labels,
    datasets: [
      {
        label: comparisonData.value.ticker1,
        data: volumes1,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: '#3b82f6',
        borderWidth: 1,
      },
      {
        label: comparisonData.value.ticker2,
        data: volumes2,
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: '#10b981',
        borderWidth: 1,
      },
    ],
  }
})

const rsiChartData = computed(() => {
  if (!comparisonData.value) return { labels: [], datasets: [] }
  
  const data1 = comparisonData.value.ticker1_data.data.filter((d) => d.rsi !== null && d.rsi !== undefined)
  const data2 = comparisonData.value.ticker2_data.data.filter((d) => d.rsi !== null && d.rsi !== undefined)
  
  const labels = data1.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const rsi1 = data1.map((d) => d.rsi!)
  const rsi2 = data2.map((d) => d.rsi!)
  
  return {
    labels,
    datasets: [
      {
        label: `${comparisonData.value.ticker1} - RSI`,
        data: rsi1,
        borderColor: '#3b82f6',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: `${comparisonData.value.ticker2} - RSI`,
        data: rsi2,
        borderColor: '#10b981',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: 'Sobrecomprado (70)',
        data: new Array(rsi1.length).fill(70),
        borderColor: '#dc2626',
        borderDash: [5, 5],
        pointRadius: 0,
      },
      {
        label: 'Sobrevendido (30)',
        data: new Array(rsi1.length).fill(30),
        borderColor: '#16a34a',
        borderDash: [5, 5],
        pointRadius: 0,
      },
    ],
  }
})

const macdChartData = computed(() => {
  if (!comparisonData.value) return { labels: [], datasets: [] }
  
  const data1 = comparisonData.value.ticker1_data.data.filter((d) => d.macd !== null && d.macd !== undefined)
  const data2 = comparisonData.value.ticker2_data.data.filter((d) => d.macd !== null && d.macd !== undefined)
  
  const labels = data1.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const macd1 = data1.map((d) => d.macd!)
  const macd2 = data2.map((d) => d.macd!)
  const signal1 = data1.map((d) => d.macd_signal || null)
  const signal2 = data2.map((d) => d.macd_signal || null)
  
  return {
    labels,
    datasets: [
      {
        label: `${comparisonData.value.ticker1} - MACD`,
        data: macd1,
        borderColor: '#3b82f6',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
      },
      {
        label: `${comparisonData.value.ticker1} - Sinal`,
        data: signal1,
        borderColor: '#60a5fa',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
      },
      {
        label: `${comparisonData.value.ticker2} - MACD`,
        data: macd2,
        borderColor: '#10b981',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
      },
      {
        label: `${comparisonData.value.ticker2} - Sinal`,
        data: signal2,
        borderColor: '#34d399',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        font: {
          size: 11,
        },
        usePointStyle: true,
        padding: 12,
      },
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      padding: 12,
      titleFont: {
        size: 13,
        weight: 'bold' as const,
      },
      bodyFont: {
        size: 12,
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

const priceChartOptions = computed(() => ({
  ...chartOptions,
  plugins: {
    ...chartOptions.plugins,
    tooltip: {
      ...chartOptions.plugins.tooltip,
      callbacks: {
        label: function (context: any) {
          return `${context.dataset.label}: ${new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(context.parsed.y)}`
        },
      },
    },
  },
  scales: {
    ...chartOptions.scales,
    y: {
      ...chartOptions.scales.y,
      ticks: {
        ...chartOptions.scales.y.ticks,
        callback: function (value: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(value)
        },
      },
    },
  },
}))

const volumeChartOptions = computed(() => ({
  ...chartOptions,
  scales: {
    ...chartOptions.scales,
    y: {
      ...chartOptions.scales.y,
      ticks: {
        ...chartOptions.scales.y.ticks,
        callback: function (value: any) {
          if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M'
          }
          if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K'
          }
          return value
        },
      },
    },
  },
}))

const rsiChartOptions = computed(() => ({
  ...chartOptions,
  scales: {
    ...chartOptions.scales,
    y: {
      min: 0,
      max: 100,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
    },
  },
}))

const macdChartOptions = computed(() => ({
  ...chartOptions,
}))

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
})
</script>

<template>
  <div class="compare-container">
    <Navbar />

    <main class="compare-main">
      <div class="search-section">
        <div class="search-card">
          <div class="header-with-icon">
            <GitCompare :size="24" />
            <h2>Comparar Tickers</h2>
          </div>
          <p class="subtitle">Compare análise técnica e fundamentos de dois ativos lado a lado</p>
          <div class="search-form">
            <div class="input-group">
              <label for="ticker1">Ticker 1</label>
              <div class="input-wrapper">
                <Search :size="20" class="input-icon" />
                <input
                  id="ticker1"
                  v-model="ticker1"
                  type="text"
                  placeholder="Ex: PETR4"
                  @keyup.enter="compareTickers"
                />
              </div>
            </div>
            <div class="input-group">
              <label for="ticker2">Ticker 2</label>
              <div class="input-wrapper">
                <Search :size="20" class="input-icon" />
                <input
                  id="ticker2"
                  v-model="ticker2"
                  type="text"
                  placeholder="Ex: VALE3"
                  @keyup.enter="compareTickers"
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
            <button @click="compareTickers" :disabled="loading" class="search-button">
              <Loader2 v-if="loading" :size="18" class="spinner" />
              <GitCompare v-else :size="18" />
              {{ loading ? 'Comparando...' : 'Comparar' }}
            </button>
          </div>
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </div>
      </div>

      <div v-if="comparisonData" class="results-section">
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

        <div v-if="activeTab === 'technical' && comparisonData" class="technical-tab">
          <!-- Indicadores Rápidos lado a lado -->
          <div class="comparison-grid indicators-section">
            <!-- Ticker 1 -->
            <div class="ticker-column">
              <div class="ticker-header">
                <h3>{{ comparisonData.ticker1 }}</h3>
                <span class="period-badge">{{ periodOptions.find(p => p.value === comparisonData.period)?.label || period }}</span>
              </div>

              <div class="indicators-grid">
                <div class="indicator-card">
                  <div class="indicator-header">
                    <TrendingUp :size="20" />
                    <span>Preço Atual</span>
                  </div>
                  <div class="indicator-value">
                    {{ lastItem1 ? formatCurrency(lastItem1.close) : 'N/A' }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <Activity :size="20" />
                    <span>RSI (14)</span>
                  </div>
                  <div class="indicator-value" :style="{ color: getRSIStatus(lastItem1?.rsi).color }">
                    {{ lastItem1?.rsi ? lastItem1.rsi.toFixed(2) : 'N/A' }}
                  </div>
                  <div class="indicator-status">
                    {{ getRSIStatus(lastItem1?.rsi).status }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <BarChart :size="20" />
                    <span>MACD</span>
                  </div>
                  <div class="indicator-value">
                    {{ lastItem1?.macd ? lastItem1.macd.toFixed(2) : 'N/A' }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <DollarSign :size="20" />
                    <span>Volume Médio</span>
                  </div>
                  <div class="indicator-value">
                    {{ formatNumber(Math.round(comparisonData.ticker1_data.data.reduce((sum, d) => sum + d.volume, 0) / comparisonData.ticker1_data.data.length)) }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Ticker 2 -->
            <div class="ticker-column">
              <div class="ticker-header">
                <h3>{{ comparisonData.ticker2 }}</h3>
                <span class="period-badge">{{ periodOptions.find(p => p.value === comparisonData.period)?.label || period }}</span>
              </div>

              <div class="indicators-grid">
                <div class="indicator-card">
                  <div class="indicator-header">
                    <TrendingUp :size="20" />
                    <span>Preço Atual</span>
                  </div>
                  <div class="indicator-value">
                    {{ lastItem2 ? formatCurrency(lastItem2.close) : 'N/A' }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <Activity :size="20" />
                    <span>RSI (14)</span>
                  </div>
                  <div class="indicator-value" :style="{ color: getRSIStatus(lastItem2?.rsi).color }">
                    {{ lastItem2?.rsi ? lastItem2.rsi.toFixed(2) : 'N/A' }}
                  </div>
                  <div class="indicator-status">
                    {{ getRSIStatus(lastItem2?.rsi).status }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <BarChart :size="20" />
                    <span>MACD</span>
                  </div>
                  <div class="indicator-value">
                    {{ lastItem2?.macd ? lastItem2.macd.toFixed(2) : 'N/A' }}
                  </div>
                </div>

                <div class="indicator-card">
                  <div class="indicator-header">
                    <DollarSign :size="20" />
                    <span>Volume Médio</span>
                  </div>
                  <div class="indicator-value">
                    {{ formatNumber(Math.round(comparisonData.ticker2_data.data.reduce((sum, d) => sum + d.volume, 0) / comparisonData.ticker2_data.data.length)) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Gráficos Comparativos -->
          <div class="charts-section">
            <div class="chart-section">
              <h4>Evolução do Preço - Comparação</h4>
              <div class="chart-card">
                <div v-if="priceChartData.labels.length > 0" class="chart-container">
                  <Line :data="priceChartData" :options="priceChartOptions" />
                </div>
                <div v-else class="chart-container empty">
                  <p>Nenhum dado disponível</p>
                </div>
              </div>
            </div>

            <div class="chart-section">
              <h4>Volume - Comparação</h4>
              <div class="chart-card">
                <div v-if="volumeChartData.labels.length > 0" class="chart-container">
                  <Bar :data="volumeChartData" :options="volumeChartOptions" />
                </div>
                <div v-else class="chart-container empty">
                  <p>Nenhum dado disponível</p>
                </div>
              </div>
            </div>

            <div class="chart-section">
              <h4>RSI (Relative Strength Index) - Comparação</h4>
              <div class="chart-card">
                <div v-if="rsiChartData.labels.length > 0" class="chart-container">
                  <Line :data="rsiChartData" :options="rsiChartOptions" />
                </div>
                <div v-else class="chart-container empty">
                  <p>Nenhum dado disponível</p>
                </div>
              </div>
            </div>

            <div class="chart-section">
              <h4>MACD (Moving Average Convergence Divergence) - Comparação</h4>
              <div class="chart-card">
                <div v-if="macdChartData.labels.length > 0" class="chart-container">
                  <Line :data="macdChartData" :options="macdChartOptions" />
                </div>
                <div v-else class="chart-container empty">
                  <p>Nenhum dado disponível</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'fundamentals' && comparisonData" class="fundamentals-tab">
          <div class="comparison-grid">
            <!-- Fundamentos Ticker 1 -->
            <div class="ticker-column">
              <div class="ticker-header">
                <h3>{{ comparisonData.ticker1 }}</h3>
              </div>

              <div class="fundamentals-grid">
                <!-- Quality Score Card -->
                <div class="fundamental-card quality-score-card" :style="{ borderColor: getQualityScoreColor(comparisonData.ticker1_fundamentals.quality_score) }">
                  <div class="fundamental-label">Score de Qualidade</div>
                  <div class="fundamental-value quality-score-value" :style="{ color: getQualityScoreColor(comparisonData.ticker1_fundamentals.quality_score) }">
                    {{ comparisonData.ticker1_fundamentals.quality_score?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="quality-score-label" :style="{ color: getQualityScoreColor(comparisonData.ticker1_fundamentals.quality_score) }">
                    {{ getQualityScoreLabel(comparisonData.ticker1_fundamentals.quality_score) }}
                  </div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/L (Price-to-Earnings)</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.pe_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/VP (Price-to-Book)</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.pb_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">EV/EBITDA</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.ev_ebitda?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/EBIT</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.pebit_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Dividend Yield</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.dividend_yield ? formatPercent(comparisonData.ticker1_fundamentals.dividend_yield * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Beta</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.beta?.toFixed(2) || 'N/A' }}</div>
                </div>

                <!-- Novas métricas de qualidade -->
                <div class="fundamental-card">
                  <div class="fundamental-label">ROE</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.roe ? formatPercent(comparisonData.ticker1_fundamentals.roe * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">ROA</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.roa ? formatPercent(comparisonData.ticker1_fundamentals.roa * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Margem Líquida</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.net_margin ? formatPercent(comparisonData.ticker1_fundamentals.net_margin * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Dívida/Patrimônio</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.debt_to_equity ? formatPercent(comparisonData.ticker1_fundamentals.debt_to_equity * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Setor</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.sector || 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Indústria</div>
                  <div class="fundamental-value">{{ comparisonData.ticker1_fundamentals.industry || 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Market Cap</div>
                  <div class="fundamental-value">
                    {{ comparisonData.ticker1_fundamentals.market_cap ? formatCurrency(comparisonData.ticker1_fundamentals.market_cap) : 'N/A' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Fundamentos Ticker 2 -->
            <div class="ticker-column">
              <div class="ticker-header">
                <h3>{{ comparisonData.ticker2 }}</h3>
              </div>

              <div class="fundamentals-grid">
                <!-- Quality Score Card -->
                <div class="fundamental-card quality-score-card" :style="{ borderColor: getQualityScoreColor(comparisonData.ticker2_fundamentals.quality_score) }">
                  <div class="fundamental-label">Score de Qualidade</div>
                  <div class="fundamental-value quality-score-value" :style="{ color: getQualityScoreColor(comparisonData.ticker2_fundamentals.quality_score) }">
                    {{ comparisonData.ticker2_fundamentals.quality_score?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="quality-score-label" :style="{ color: getQualityScoreColor(comparisonData.ticker2_fundamentals.quality_score) }">
                    {{ getQualityScoreLabel(comparisonData.ticker2_fundamentals.quality_score) }}
                  </div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/L (Price-to-Earnings)</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.pe_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/VP (Price-to-Book)</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.pb_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">EV/EBITDA</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.ev_ebitda?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">P/EBIT</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.pebit_ratio?.toFixed(2) || 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Dividend Yield</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.dividend_yield ? formatPercent(comparisonData.ticker2_fundamentals.dividend_yield * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Beta</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.beta?.toFixed(2) || 'N/A' }}</div>
                </div>

                <!-- Novas métricas de qualidade -->
                <div class="fundamental-card">
                  <div class="fundamental-label">ROE</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.roe ? formatPercent(comparisonData.ticker2_fundamentals.roe * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">ROA</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.roa ? formatPercent(comparisonData.ticker2_fundamentals.roa * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Margem Líquida</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.net_margin ? formatPercent(comparisonData.ticker2_fundamentals.net_margin * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card">
                  <div class="fundamental-label">Dívida/Patrimônio</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.debt_to_equity ? formatPercent(comparisonData.ticker2_fundamentals.debt_to_equity * 100) : 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Setor</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.sector || 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Indústria</div>
                  <div class="fundamental-value">{{ comparisonData.ticker2_fundamentals.industry || 'N/A' }}</div>
                </div>

                <div class="fundamental-card full-width">
                  <div class="fundamental-label">Market Cap</div>
                  <div class="fundamental-value">
                    {{ comparisonData.ticker2_fundamentals.market_cap ? formatCurrency(comparisonData.ticker2_fundamentals.market_cap) : 'N/A' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!loading && !error" class="empty-state">
        <GitCompare :size="64" class="empty-icon" />
        <h3>Compare dois tickers</h3>
        <p>Digite dois tickers diferentes e selecione o período para visualizar a comparação lado a lado</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/compare.css';
</style>

