<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type TechnicalAnalysis, type AdvancedAnalysis, type WavePoint, type ElliottAnnotation } from '../services/api/index'
import { 
  Search, BarChart, TrendingUp, TrendingDown, Loader2, X, Eye, EyeOff, 
  Save, Trash2, Download, Upload, Edit2, Crown, AlertCircle, 
  Settings, Layers, Activity, Zap, Target, ChevronRight, Info
} from 'lucide-vue-next'
import AdvancedPriceChart from '../components/AdvancedPriceChart.vue'
import ElliottWaveEditor from '../components/ElliottWaveEditor.vue'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const ticker = ref('')
const period = ref('1y')
const loading = ref(false)
const error = ref('')
const technicalData = ref<TechnicalAnalysis | null>(null)
const advancedAnalysis = ref<AdvancedAnalysis | null>(null)
const manualElliottWaves = ref<WavePoint[]>([])
const savedElliottAnnotation = ref<ElliottAnnotation | null>(null)
const isEditMode = ref(false)
const currentWave = ref('1')
const savingAnnotations = ref(false)
const activeTab = ref<'patterns' | 'support' | 'fibonacci' | 'candlestick' | 'elliott'>('patterns')
const sidebarLeftCollapsed = ref(false)
const sidebarRightCollapsed = ref(false)

// Toggles para mostrar/ocultar elementos
const showSupportResistance = ref(true)
const showFibonacci = ref(true)
const showPatterns = ref(true)
const showElliottWaves = ref(true)
const showCandlestickPatterns = ref(true)

const isPro = computed(() => authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN')

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

const availableWaves = ['1', '2', '3', '4', '5', 'A', 'B', 'C']

// Computed para estatísticas
const summaryStats = computed(() => {
  if (!advancedAnalysis.value) return null
  
  const totalPatterns = advancedAnalysis.value.patterns.length
  const totalCandlestick = advancedAnalysis.value.candlestick_patterns.length
  const avgConfidence = advancedAnalysis.value.patterns.length > 0
    ? advancedAnalysis.value.patterns.reduce((sum, p) => sum + p.confidence, 0) / advancedAnalysis.value.patterns.length
    : 0
  
  return {
    totalPatterns,
    totalCandlestick,
    supportLevels: advancedAnalysis.value.support_levels.length,
    resistanceLevels: advancedAnalysis.value.resistance_levels.length,
    avgConfidence: Math.round(avgConfidence * 100),
    hasElliottWaves: advancedAnalysis.value.elliott_waves.waves.length > 0
  }
})

async function searchTicker() {
  if (!ticker.value.trim()) {
    error.value = 'Por favor, digite um ticker'
    return
  }

  if (!isPro.value) {
    error.value = 'Esta funcionalidade é exclusiva para usuários PRO'
    router.push('/subscription')
    return
  }

  error.value = ''
  loading.value = true
  technicalData.value = null
  advancedAnalysis.value = null
  manualElliottWaves.value = []
  savedElliottAnnotation.value = null

  try {
    const [techAnalysis, advAnalysis] = await Promise.all([
      api.getTechnicalAnalysis(ticker.value.toUpperCase(), period.value),
      api.getAdvancedAnalysis(ticker.value.toUpperCase(), period.value),
    ])

    technicalData.value = techAnalysis
    advancedAnalysis.value = advAnalysis

    // Carregar anotações salvas de Elliott
    await loadElliottAnnotations()
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 402) {
        error.value = 'Esta funcionalidade requer assinatura PRO'
        router.push('/subscription')
      } else {
        error.value = err.message
      }
    } else {
      error.value = 'Erro ao buscar dados. Tente novamente.'
    }
  } finally {
    loading.value = false
  }
}

async function loadElliottAnnotations() {
  if (!ticker.value || !isPro.value) return

  try {
    const annotation = await api.getElliottAnnotations(ticker.value.toUpperCase(), period.value)
    if (annotation) {
      savedElliottAnnotation.value = annotation
      manualElliottWaves.value = annotation.annotations
    }
  } catch (err) {
    // Ignorar erro se não houver anotações salvas
    console.log('Nenhuma anotação salva encontrada')
  }
}

async function saveElliottAnnotations() {
  if (!ticker.value || !isPro.value || manualElliottWaves.value.length === 0) return

  savingAnnotations.value = true
  try {
    const annotation = await api.saveElliottAnnotations({
      ticker: ticker.value.toUpperCase(),
      period: period.value,
      annotations: manualElliottWaves.value,
    })
    savedElliottAnnotation.value = annotation
    error.value = ''
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao salvar anotações'
    }
  } finally {
    savingAnnotations.value = false
  }
}

async function deleteElliottAnnotations() {
  if (!ticker.value || !isPro.value) return

  if (!confirm('Tem certeza que deseja deletar todas as anotações?')) {
    return
  }

  savingAnnotations.value = true
  try {
    await api.deleteElliottAnnotations(ticker.value.toUpperCase(), period.value)
    manualElliottWaves.value = []
    savedElliottAnnotation.value = null
    error.value = ''
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao deletar anotações'
    }
  } finally {
    savingAnnotations.value = false
  }
}

function handleChartClick(event: any) {
  if (!isEditMode.value || !technicalData.value || !event.chart) return

  const canvasPosition = event.native
  const chart = event.chart
  const dataX = chart.scales.x.getValueForPixel(canvasPosition.x)
  const dataY = chart.scales.y.getValueForPixel(canvasPosition.y)

  if (dataX >= 0 && dataX < technicalData.value.data.length) {
    const dataPoint = technicalData.value.data[dataX]
    const date = dataPoint.date
    const price = dataY

    // Adicionar ou atualizar anotação para a onda atual
    const existingIndex = manualElliottWaves.value.findIndex(
      (ann) => ann.wave === currentWave.value && ann.date === date
    )

    if (existingIndex >= 0) {
      manualElliottWaves.value[existingIndex].price = price
    } else {
      manualElliottWaves.value.push({
        wave: currentWave.value,
        date: date,
        price: price,
      })
    }

    // Ordenar por data
    manualElliottWaves.value.sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    )
  }
}

function handleEditorSave(annotations: WavePoint[]) {
  manualElliottWaves.value = annotations
  saveElliottAnnotations()
}

function handleEditorDelete() {
  deleteElliottAnnotations()
}

function handleEditorLoad(annotations: WavePoint[]) {
  manualElliottWaves.value = annotations
}

function handleToggleEdit() {
  isEditMode.value = !isEditMode.value
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

  // Verificar se é PRO
  if (!isPro.value) {
    router.push('/subscription')
    return
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
  <div class="advanced-analysis-container">
    <Navbar />

    <main class="advanced-analysis-main">
      <!-- Header Redesenhado -->
      <div class="page-header">
        <div class="header-content">
          <div class="header-left">
            <div class="title-section">
              <div class="title-with-badge">
                <h1>Análise Técnica Avançada</h1>
                <span class="pro-badge">
                  <Crown :size="14" />
                  PRO
                </span>
              </div>
              <p class="subtitle">Detecção automática de padrões, suporte/resistência, Fibonacci e ondas de Elliott</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Search Section Compacta -->
      <div class="search-section">
        <div class="search-card">
          <div class="search-form">
            <div class="input-group">
              <label for="ticker">Ticker</label>
              <div class="input-wrapper">
                <Search :size="18" class="input-icon" />
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
              <Loader2 v-if="loading" :size="18" class="spinner" />
              <Search v-else :size="18" />
              {{ loading ? 'Buscando...' : 'Buscar' }}
            </button>
          </div>
          <div v-if="error" class="error-message">
            <AlertCircle :size="16" />
            {{ error }}
          </div>
        </div>
      </div>

      <!-- Layout Principal em Grid -->
      <div v-if="technicalData && advancedAnalysis" class="main-grid">
        <!-- Sidebar Esquerda -->
        <aside class="sidebar-left" :class="{ collapsed: sidebarLeftCollapsed }">
          <div class="sidebar-header">
            <h3>Controles</h3>
            <button @click="sidebarLeftCollapsed = !sidebarLeftCollapsed" class="collapse-btn">
              <ChevronRight :size="16" :class="{ rotated: sidebarLeftCollapsed }" />
            </button>
          </div>
          
          <div class="sidebar-content">
            <!-- Toggles de Visualização -->
            <div class="control-section">
              <h4>Visualização</h4>
              <div class="toggle-list">
                <label class="toggle-item">
                  <input type="checkbox" v-model="showSupportResistance" />
                  <span>Suporte/Resistência</span>
                  <Eye v-if="showSupportResistance" :size="16" class="toggle-icon" />
                  <EyeOff v-else :size="16" class="toggle-icon" />
                </label>
                <label class="toggle-item">
                  <input type="checkbox" v-model="showFibonacci" />
                  <span>Fibonacci</span>
                  <Eye v-if="showFibonacci" :size="16" class="toggle-icon" />
                  <EyeOff v-else :size="16" class="toggle-icon" />
                </label>
                <label class="toggle-item">
                  <input type="checkbox" v-model="showPatterns" />
                  <span>Padrões Gráficos</span>
                  <Eye v-if="showPatterns" :size="16" class="toggle-icon" />
                  <EyeOff v-else :size="16" class="toggle-icon" />
                </label>
                <label class="toggle-item">
                  <input type="checkbox" v-model="showElliottWaves" />
                  <span>Ondas de Elliott</span>
                  <Eye v-if="showElliottWaves" :size="16" class="toggle-icon" />
                  <EyeOff v-else :size="16" class="toggle-icon" />
                </label>
                <label class="toggle-item">
                  <input type="checkbox" v-model="showCandlestickPatterns" />
                  <span>Candlestick</span>
                  <Eye v-if="showCandlestickPatterns" :size="16" class="toggle-icon" />
                  <EyeOff v-else :size="16" class="toggle-icon" />
                </label>
              </div>
            </div>

            <!-- Seletor de Onda (quando em modo edição) -->
            <div v-if="isEditMode" class="control-section">
              <h4>Onda Atual</h4>
              <div class="wave-selector-grid">
                <button
                  v-for="wave in availableWaves"
                  :key="wave"
                  @click="currentWave = wave"
                  :class="['wave-btn', { active: currentWave === wave }]"
                >
                  {{ wave }}
                </button>
              </div>
            </div>

            <!-- Editor de Elliott Waves -->
            <div class="control-section elliott-section">
              <ElliottWaveEditor
                :annotations="manualElliottWaves"
                :is-edit-mode="isEditMode"
                :is-loading="savingAnnotations"
                @save="handleEditorSave"
                @delete="handleEditorDelete"
                @load="handleEditorLoad"
                @toggle-edit="handleToggleEdit"
              />
            </div>
          </div>
        </aside>

        <!-- Área Central - Gráfico e Tabs -->
        <div class="main-content">
          <!-- Toolbar do Gráfico -->
          <div class="chart-toolbar">
            <div class="toolbar-left">
              <h2>{{ advancedAnalysis.ticker }}</h2>
              <span class="period-badge">{{ periodOptions.find(p => p.value === period)?.label }}</span>
            </div>
            <div class="toolbar-right">
              <button 
                @click="isEditMode = !isEditMode"
                :class="['toolbar-btn', { active: isEditMode }]"
                title="Modo de Edição"
              >
                <Edit2 :size="16" />
                {{ isEditMode ? 'Editando' : 'Editar' }}
              </button>
            </div>
          </div>

          <!-- Gráfico Principal -->
          <div class="chart-section">
            <AdvancedPriceChart
              :technical-data="technicalData"
              :advanced-analysis="advancedAnalysis"
              :manual-elliott-waves="manualElliottWaves"
              :show-support-resistance="showSupportResistance"
              :show-fibonacci="showFibonacci"
              :show-patterns="showPatterns"
              :show-elliott-waves="showElliottWaves"
              :show-candlestick-patterns="showCandlestickPatterns"
              :edit-mode="isEditMode"
              :on-chart-click="handleChartClick"
            />
          </div>

          <!-- Tabs de Análise -->
          <div class="analysis-tabs">
            <button
              @click="activeTab = 'patterns'"
              :class="['tab-btn', { active: activeTab === 'patterns' }]"
            >
              <Layers :size="16" />
              Padrões Gráficos
              <span v-if="advancedAnalysis.patterns.length > 0" class="tab-badge">
                {{ advancedAnalysis.patterns.length }}
              </span>
            </button>
            <button
              @click="activeTab = 'support'"
              :class="['tab-btn', { active: activeTab === 'support' }]"
            >
              <Target :size="16" />
              Suporte/Resistência
              <span v-if="(advancedAnalysis.support_levels.length + advancedAnalysis.resistance_levels.length) > 0" class="tab-badge">
                {{ advancedAnalysis.support_levels.length + advancedAnalysis.resistance_levels.length }}
              </span>
            </button>
            <button
              @click="activeTab = 'fibonacci'"
              :class="['tab-btn', { active: activeTab === 'fibonacci' }]"
            >
              <Activity :size="16" />
              Fibonacci
            </button>
            <button
              @click="activeTab = 'candlestick'"
              :class="['tab-btn', { active: activeTab === 'candlestick' }]"
            >
              <Zap :size="16" />
              Candlestick
              <span v-if="advancedAnalysis.candlestick_patterns.length > 0" class="tab-badge">
                {{ advancedAnalysis.candlestick_patterns.length }}
              </span>
            </button>
            <button
              @click="activeTab = 'elliott'"
              :class="['tab-btn', { active: activeTab === 'elliott' }]"
            >
              <BarChart :size="16" />
              Elliott Waves
            </button>
          </div>

          <!-- Conteúdo das Tabs -->
          <div class="tab-content">
            <!-- Tab: Padrões Gráficos -->
            <div v-if="activeTab === 'patterns'" class="tab-panel">
              <div v-if="advancedAnalysis.patterns.length === 0" class="empty-state-panel">
                <Layers :size="48" class="empty-icon" />
                <h3>Nenhum padrão gráfico detectado</h3>
                <p>Tente ajustar o período ou buscar outro ativo</p>
              </div>
              <div v-else class="patterns-grid">
                <div
                  v-for="(pattern, idx) in advancedAnalysis.patterns"
                  :key="idx"
                  class="pattern-card"
                  :class="pattern.trend?.toLowerCase()"
                >
                  <div class="pattern-card-header">
                    <div class="pattern-icon-wrapper" :class="pattern.trend?.toLowerCase()">
                      <TrendingUp v-if="pattern.trend === 'BULLISH'" :size="20" />
                      <TrendingDown v-else-if="pattern.trend === 'BEARISH'" :size="20" />
                      <Activity v-else :size="20" />
                    </div>
                    <div class="pattern-info">
                      <h4>{{ pattern.pattern_name }}</h4>
                      <span class="pattern-type">{{ pattern.pattern_type }}</span>
                    </div>
                    <div class="confidence-badge" :class="pattern.confidence > 0.6 ? 'high' : pattern.confidence > 0.4 ? 'medium' : 'low'">
                      {{ (pattern.confidence * 100).toFixed(0) }}%
                    </div>
                  </div>
                  <div class="pattern-card-body">
                    <div class="pattern-detail">
                      <span class="detail-label">Período:</span>
                      <span class="detail-value">
                        {{ new Date(pattern.start_date).toLocaleDateString('pt-BR') }} - 
                        {{ new Date(pattern.end_date).toLocaleDateString('pt-BR') }}
                      </span>
                    </div>
                    <div v-if="pattern.head_price" class="pattern-detail">
                      <span class="detail-label">Preço da Cabeça:</span>
                      <span class="detail-value">
                        {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(pattern.head_price) }}
                      </span>
                    </div>
                    <div v-if="pattern.neckline" class="pattern-detail">
                      <span class="detail-label">Linha de Pescoço:</span>
                      <span class="detail-value">
                        {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(pattern.neckline) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab: Suporte/Resistência -->
            <div v-if="activeTab === 'support'" class="tab-panel">
              <div class="levels-container">
                <div class="levels-column">
                  <div class="column-header support">
                    <Target :size="18" />
                    <h3>Níveis de Suporte</h3>
                    <span class="count-badge">{{ advancedAnalysis.support_levels.length }}</span>
                  </div>
                  <div v-if="advancedAnalysis.support_levels.length === 0" class="empty-state-panel">
                    <p>Nenhum nível de suporte identificado</p>
                  </div>
                  <div v-else class="levels-list">
                    <div
                      v-for="(level, idx) in advancedAnalysis.support_levels"
                      :key="idx"
                      class="level-card support"
                    >
                      <div class="level-main">
                        <span class="level-price">
                          {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(level.price) }}
                        </span>
                        <div class="level-meta">
                          <span class="strength-indicator" :style="{ width: `${level.strength * 100}%` }"></span>
                          <span class="strength-text">Força: {{ (level.strength * 100).toFixed(0) }}%</span>
                        </div>
                      </div>
                      <div class="level-details">
                        <div class="level-stat">
                          <span class="stat-label">Testes:</span>
                          <span class="stat-value">{{ level.test_count }}</span>
                        </div>
                        <div class="level-stat">
                          <span class="stat-label">Distância:</span>
                          <span class="stat-value">{{ level.distance_from_current.toFixed(2) }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="levels-column">
                  <div class="column-header resistance">
                    <Target :size="18" />
                    <h3>Níveis de Resistência</h3>
                    <span class="count-badge">{{ advancedAnalysis.resistance_levels.length }}</span>
                  </div>
                  <div v-if="advancedAnalysis.resistance_levels.length === 0" class="empty-state-panel">
                    <p>Nenhum nível de resistência identificado</p>
                  </div>
                  <div v-else class="levels-list">
                    <div
                      v-for="(level, idx) in advancedAnalysis.resistance_levels"
                      :key="idx"
                      class="level-card resistance"
                    >
                      <div class="level-main">
                        <span class="level-price">
                          {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(level.price) }}
                        </span>
                        <div class="level-meta">
                          <span class="strength-indicator" :style="{ width: `${level.strength * 100}%` }"></span>
                          <span class="strength-text">Força: {{ (level.strength * 100).toFixed(0) }}%</span>
                        </div>
                      </div>
                      <div class="level-details">
                        <div class="level-stat">
                          <span class="stat-label">Testes:</span>
                          <span class="stat-value">{{ level.test_count }}</span>
                        </div>
                        <div class="level-stat">
                          <span class="stat-label">Distância:</span>
                          <span class="stat-value">{{ level.distance_from_current.toFixed(2) }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab: Fibonacci -->
            <div v-if="activeTab === 'fibonacci'" class="tab-panel">
              <div v-if="!advancedAnalysis.fibonacci_levels || Object.keys(advancedAnalysis.fibonacci_levels).length === 0" class="empty-state-panel">
                <Activity :size="48" class="empty-icon" />
                <h3>Nenhum nível de Fibonacci calculado</h3>
              </div>
              <div v-else class="fibonacci-container">
                <div class="fibonacci-info">
                  <div class="fib-info-card">
                    <span class="fib-label">Swing High</span>
                    <span class="fib-value">
                      {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(advancedAnalysis.fibonacci_levels.swing_high) }}
                    </span>
                  </div>
                  <div class="fib-info-card">
                    <span class="fib-label">Swing Low</span>
                    <span class="fib-value">
                      {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(advancedAnalysis.fibonacci_levels.swing_low) }}
                    </span>
                  </div>
                </div>
                <div class="fibonacci-levels">
                  <div
                    v-for="(value, key) in advancedAnalysis.fibonacci_levels"
                    :key="key"
                    v-if="key.startsWith('level_')"
                    class="fib-level-card"
                  >
                    <div class="fib-level-header">
                      <span class="fib-percentage">{{ key.replace('level_', '').replace(/(\d)(\d{2})$/, '$1.$2') }}%</span>
                      <span class="fib-price">
                        {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab: Candlestick -->
            <div v-if="activeTab === 'candlestick'" class="tab-panel">
              <div v-if="advancedAnalysis.candlestick_patterns.length === 0" class="empty-state-panel">
                <Zap :size="48" class="empty-icon" />
                <h3>Nenhum padrão de candlestick detectado</h3>
              </div>
              <div v-else class="candlestick-grid">
                <div
                  v-for="(pattern, idx) in advancedAnalysis.candlestick_patterns"
                  :key="idx"
                  class="candlestick-card"
                  :class="pattern.signal.toLowerCase()"
                >
                  <div class="candlestick-header">
                    <div class="signal-icon" :class="pattern.signal.toLowerCase()">
                      <TrendingUp v-if="pattern.signal === 'BULLISH'" :size="20" />
                      <TrendingDown v-else-if="pattern.signal === 'BEARISH'" :size="20" />
                      <Activity v-else :size="20" />
                    </div>
                    <div class="candlestick-info">
                      <h4>{{ pattern.pattern_name }}</h4>
                      <span class="pattern-date">{{ new Date(pattern.date).toLocaleDateString('pt-BR') }}</span>
                    </div>
                    <span class="signal-badge" :class="pattern.signal.toLowerCase()">
                      {{ pattern.signal }}
                    </span>
                  </div>
                  <div class="candlestick-price">
                    {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(pattern.price) }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab: Elliott Waves -->
            <div v-if="activeTab === 'elliott'" class="tab-panel">
              <div class="elliott-container">
                <div v-if="advancedAnalysis.elliott_waves.pattern_type" class="elliott-summary-card">
                  <div class="summary-header">
                    <BarChart :size="24" />
                    <div>
                      <h3>Padrão Detectado</h3>
                      <p class="pattern-type-text">{{ advancedAnalysis.elliott_waves.pattern_type }}</p>
                    </div>
                    <div class="confidence-display">
                      <span class="confidence-label">Confiança</span>
                      <span class="confidence-value">{{ (advancedAnalysis.elliott_waves.confidence * 100).toFixed(0) }}%</span>
                    </div>
                  </div>
                  <div v-if="advancedAnalysis.elliott_waves.waves.length > 0" class="waves-preview">
                    <div
                      v-for="(wave, idx) in advancedAnalysis.elliott_waves.waves"
                      :key="idx"
                      class="wave-preview-item"
                    >
                      <span class="wave-label">{{ wave.wave }}</span>
                      <span class="wave-date">{{ new Date(wave.date).toLocaleDateString('pt-BR') }}</span>
                      <span class="wave-price">
                        {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(wave.price) }}
                      </span>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-state-panel">
                  <BarChart :size="48" class="empty-icon" />
                  <h3>Nenhum padrão de ondas de Elliott detectado automaticamente</h3>
                  <p>Use o editor manual na sidebar para adicionar suas próprias anotações</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Direita - Resumo -->
        <aside class="sidebar-right" :class="{ collapsed: sidebarRightCollapsed }">
          <div class="sidebar-header">
            <h3>Resumo</h3>
            <button @click="sidebarRightCollapsed = !sidebarRightCollapsed" class="collapse-btn">
              <ChevronRight :size="16" :class="{ rotated: !sidebarRightCollapsed }" />
            </button>
          </div>
          
          <div class="sidebar-content">
            <div v-if="summaryStats" class="summary-section">
              <div class="stat-card">
                <div class="stat-icon patterns">
                  <Layers :size="20" />
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ summaryStats.totalPatterns }}</span>
                  <span class="stat-label">Padrões Gráficos</span>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon candlestick">
                  <Zap :size="20" />
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ summaryStats.totalCandlestick }}</span>
                  <span class="stat-label">Candlestick</span>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon support">
                  <Target :size="20" />
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ summaryStats.supportLevels }}</span>
                  <span class="stat-label">Suportes</span>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon resistance">
                  <Target :size="20" />
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ summaryStats.resistanceLevels }}</span>
                  <span class="stat-label">Resistências</span>
                </div>
              </div>
              <div v-if="summaryStats.avgConfidence > 0" class="stat-card">
                <div class="stat-icon confidence">
                  <Activity :size="20" />
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ summaryStats.avgConfidence }}%</span>
                  <span class="stat-label">Confiança Média</span>
                </div>
              </div>
            </div>

            <!-- Padrões Mais Importantes -->
            <div v-if="advancedAnalysis.patterns.length > 0" class="summary-section">
              <h4>Padrões Principais</h4>
              <div class="quick-patterns">
                <div
                  v-for="(pattern, idx) in advancedAnalysis.patterns.slice(0, 3)"
                  :key="idx"
                  class="quick-pattern-item"
                  @click="activeTab = 'patterns'"
                >
                  <div class="quick-pattern-icon" :class="pattern.trend?.toLowerCase()">
                    <TrendingUp v-if="pattern.trend === 'BULLISH'" :size="14" />
                    <TrendingDown v-else-if="pattern.trend === 'BEARISH'" :size="14" />
                    <Activity v-else :size="14" />
                  </div>
                  <div class="quick-pattern-info">
                    <span class="quick-pattern-name">{{ pattern.pattern_name }}</span>
                    <span class="quick-pattern-confidence">{{ (pattern.confidence * 100).toFixed(0) }}%</span>
                  </div>
                  <ChevronRight :size="16" class="chevron" />
                </div>
              </div>
            </div>

            <!-- Links Rápidos -->
            <div class="summary-section">
              <h4>Navegação Rápida</h4>
              <div class="quick-links">
                <button @click="activeTab = 'patterns'" class="quick-link">
                  <Layers :size="16" />
                  Padrões Gráficos
                </button>
                <button @click="activeTab = 'support'" class="quick-link">
                  <Target :size="16" />
                  Suporte/Resistência
                </button>
                <button @click="activeTab = 'fibonacci'" class="quick-link">
                  <Activity :size="16" />
                  Fibonacci
                </button>
                <button @click="activeTab = 'candlestick'" class="quick-link">
                  <Zap :size="16" />
                  Candlestick
                </button>
                <button @click="activeTab = 'elliott'" class="quick-link">
                  <BarChart :size="16" />
                  Elliott Waves
                </button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading && !error" class="empty-state">
        <div class="empty-content">
          <BarChart :size="80" class="empty-icon" />
          <h2>Busque um ativo para análise avançada</h2>
          <p>Digite o ticker de uma ação e selecione o período para visualizar padrões técnicos avançados</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/advanced-analysis.css';
</style>
