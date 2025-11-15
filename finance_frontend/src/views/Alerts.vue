<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type AlertListResponse, type AlertCreate } from '../services/api/index'
import { Bell, Plus, Trash2, Loader2, AlertCircle, Search, X, Power, PowerOff, TrendingUp } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()

const alerts = ref<AlertListResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const creating = ref(false)
const toggling = ref<number | null>(null)
const deleting = ref<number | null>(null)
const showAddForm = ref(false)

const newAlert = ref<AlertCreate>({
  ticker: '',
  indicator_type: 'RSI',
  condition: 'GREATER_THAN',
  threshold_value: undefined,
})

const indicatorOptions = [
  { value: 'MACD', label: 'MACD' },
  { value: 'RSI', label: 'RSI' },
  { value: 'STOCHASTIC', label: 'Stochastic' },
  { value: 'BBANDS', label: 'Bollinger Bands' },
]

const conditionOptions = [
  { value: 'CROSS_ABOVE', label: 'Cruzar Acima' },
  { value: 'CROSS_BELOW', label: 'Cruzar Abaixo' },
  { value: 'GREATER_THAN', label: 'Maior Que' },
  { value: 'LESS_THAN', label: 'Menor Que' },
]

const needsThreshold = computed(() => {
  return ['GREATER_THAN', 'LESS_THAN'].includes(newAlert.value.condition)
})

const activeAlerts = computed(() => {
  if (!alerts.value) return []
  return alerts.value.alerts.filter(alert => alert.is_active)
})

const inactiveAlerts = computed(() => {
  if (!alerts.value) return []
  return alerts.value.alerts.filter(alert => !alert.is_active)
})

const triggeredAlerts = computed(() => {
  if (!alerts.value) return []
  return alerts.value.alerts.filter(alert => alert.triggered_at)
})

const isPro = computed(() => {
  return authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN'
})

const canCreateAlert = computed(() => {
  if (isPro.value) return true
  if (!alerts.value) return true
  return alerts.value.alerts.length < 1
})

async function loadAlerts() {
  loading.value = true
  error.value = null
  try {
    alerts.value = await api.getAlerts()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao carregar alertas. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function createAlert() {
  if (!newAlert.value.ticker.trim()) {
    error.value = 'Por favor, digite um ticker'
    return
  }

  if (needsThreshold.value && (!newAlert.value.threshold_value || newAlert.value.threshold_value <= 0)) {
    error.value = 'Por favor, informe um valor limite válido'
    return
  }

  // Verificar se usuário pode criar alerta
  if (!canCreateAlert.value) {
    error.value = 'Usuários grátis podem criar apenas 1 alerta. Faça upgrade para PRO para criar alertas ilimitados.'
    router.push('/subscription')
    return
  }

  creating.value = true
  error.value = null

  try {
    const alertData: AlertCreate = {
      ticker: newAlert.value.ticker.toUpperCase().trim(),
      indicator_type: newAlert.value.indicator_type,
      condition: newAlert.value.condition,
    }

    if (needsThreshold.value && newAlert.value.threshold_value) {
      alertData.threshold_value = newAlert.value.threshold_value
    }

    await api.createAlert(alertData)
    
    // Reset form
    newAlert.value = {
      ticker: '',
      indicator_type: 'RSI',
      condition: 'GREATER_THAN',
      threshold_value: undefined,
    }
    showAddForm.value = false
    await loadAlerts()
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 402) {
        // Payment Required - redirecionar para subscription
        error.value = 'Usuários grátis podem criar apenas 1 alerta. Faça upgrade para PRO para criar alertas ilimitados.'
        router.push('/subscription')
      } else {
        error.value = err.message
      }
    } else {
      error.value = 'Erro ao criar alerta. Tente novamente.'
    }
    console.error(err)
  } finally {
    creating.value = false
  }
}

async function toggleAlert(alertId: number) {
  toggling.value = alertId
  error.value = null

  try {
    await api.toggleAlert(alertId)
    await loadAlerts()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao alterar status do alerta. Tente novamente.'
    }
    console.error(err)
  } finally {
    toggling.value = null
  }
}

async function deleteAlert(alertId: number) {
  const alert = alerts.value?.alerts.find(a => a.id === alertId)
  if (!confirm(`Deseja remover o alerta para ${alert?.ticker}?`)) {
    return
  }

  deleting.value = alertId
  error.value = null

  try {
    await api.deleteAlert(alertId)
    await loadAlerts()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao remover alerta. Tente novamente.'
    }
    console.error(err)
  } finally {
    deleting.value = null
  }
}

function goToAnalysis(ticker: string) {
  router.push(`/market-analysis?ticker=${ticker}`)
}

function formatCondition(condition: string): string {
  const mapping: Record<string, string> = {
    CROSS_ABOVE: 'Cruzar Acima',
    CROSS_BELOW: 'Cruzar Abaixo',
    GREATER_THAN: 'Maior Que',
    LESS_THAN: 'Menor Que',
  }
  return mapping[condition] || condition
}

function formatIndicator(indicator: string): string {
  const mapping: Record<string, string> = {
    MACD: 'MACD',
    RSI: 'RSI',
    STOCHASTIC: 'Stochastic',
    BBANDS: 'Bollinger Bands',
  }
  return mapping[indicator] || indicator
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

  await loadAlerts()
})
</script>

<template>
  <div class="alerts-container">
    <Navbar />

    <main class="alerts-main">
      <div class="header-section">
        <div class="header-content">
          <div class="title-group">
            <Bell :size="32" class="title-icon" />
            <div>
              <h1>Meus Alertas</h1>
              <p class="subtitle">Configure alertas para monitorar o mercado</p>
            </div>
          </div>
          <button 
            @click="!canCreateAlert ? router.push('/subscription') : showAddForm = !showAddForm" 
            class="add-button"
            :class="{ 'disabled': !canCreateAlert && !isPro }"
          >
            <Plus :size="20" />
            <span>{{ !canCreateAlert && !isPro ? 'Upgrade para PRO' : 'Novo Alerta' }}</span>
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div v-if="alerts && alerts.alerts.length > 0" class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <Bell :size="20" class="stat-icon" />
            <h3>Total</h3>
          </div>
          <p class="stat-value">{{ alerts.alerts.length }}</p>
        </div>
        <div class="stat-card active">
          <div class="stat-header">
            <Power :size="20" class="stat-icon" />
            <h3>Ativos</h3>
          </div>
          <p class="stat-value">{{ activeAlerts.length }}</p>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <AlertCircle :size="20" class="stat-icon" />
            <h3>Disparados</h3>
          </div>
          <p class="stat-value">{{ triggeredAlerts.length }}</p>
        </div>
      </div>

      <!-- Add Form -->
      <div v-if="showAddForm" class="add-form-card">
        <div class="form-header">
          <h3>Criar Novo Alerta</h3>
          <button @click="showAddForm = false" class="close-button">
            <X :size="20" />
          </button>
        </div>
        <div class="form-content">
          <div class="form-grid">
            <div class="input-group">
              <label for="alert-ticker">Ticker</label>
              <div class="input-wrapper">
                <Search :size="20" class="input-icon" />
                <input
                  id="alert-ticker"
                  v-model="newAlert.ticker"
                  type="text"
                  placeholder="Ex: PETR4, AAPL"
                  :disabled="creating"
                />
              </div>
            </div>

            <div class="input-group">
              <label for="indicator-type">Indicador</label>
              <select id="indicator-type" v-model="newAlert.indicator_type" :disabled="creating">
                <option v-for="opt in indicatorOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div class="input-group">
              <label for="condition">Condição</label>
              <select id="condition" v-model="newAlert.condition" :disabled="creating">
                <option v-for="opt in conditionOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div v-if="needsThreshold" class="input-group">
              <label for="threshold">Valor Limite</label>
              <input
                id="threshold"
                v-model.number="newAlert.threshold_value"
                type="number"
                step="0.01"
                placeholder="Ex: 70.0"
                :disabled="creating"
              />
            </div>
          </div>

          <div class="form-actions">
            <button @click="createAlert" :disabled="creating || !newAlert.ticker.trim()" class="submit-button">
              <Loader2 v-if="creating" :size="16" class="spinner" />
              <span>{{ creating ? 'Criando...' : 'Criar Alerta' }}</span>
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
        <p>Carregando alertas...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!alerts || alerts.alerts.length === 0" class="empty-state">
        <Bell :size="64" class="empty-icon" />
        <h2>Nenhum alerta configurado</h2>
        <p>Configure alertas para receber notificações sobre movimentos do mercado</p>
        <button 
          @click="!canCreateAlert ? router.push('/subscription') : showAddForm = true" 
          class="empty-action-button"
        >
          <Plus :size="20" />
          <span>{{ !canCreateAlert && !isPro ? 'Upgrade para PRO' : 'Criar Primeiro Alerta' }}</span>
        </button>
      </div>

      <!-- Alerts List -->
      <div v-else class="alerts-content">
        <!-- Active Alerts -->
        <div v-if="activeAlerts.length > 0" class="alerts-section">
          <h2 class="section-title">
            <Power :size="24" />
            <span>Alertas Ativos</span>
            <span class="badge">{{ activeAlerts.length }}</span>
          </h2>
          <div class="alerts-grid">
            <div
              v-for="alert in activeAlerts"
              :key="alert.id"
              class="alert-card active"
            >
              <div class="alert-header">
                <div class="alert-info">
                  <h3 class="alert-ticker">{{ alert.ticker }}</h3>
                  <span class="alert-meta">
                    {{ formatIndicator(alert.indicator_type) }} • {{ formatCondition(alert.condition) }}
                    <span v-if="alert.threshold_value !== null && alert.threshold_value !== undefined">
                      {{ alert.threshold_value }}
                    </span>
                  </span>
                </div>
                <div class="alert-badge active-badge">
                  <Power :size="14" />
                  <span>Ativo</span>
                </div>
              </div>
              <div v-if="alert.triggered_at" class="triggered-info">
                <AlertCircle :size="16" />
                <span>Disparado em {{ new Date(alert.triggered_at).toLocaleString('pt-BR') }}</span>
              </div>
              <div class="alert-actions">
                <button @click="goToAnalysis(alert.ticker)" class="action-button">
                  <TrendingUp :size="16" />
                  <span>Ver Análise</span>
                </button>
                <button
                  @click="toggleAlert(alert.id)"
                  :disabled="toggling === alert.id"
                  class="toggle-button"
                  title="Desativar"
                >
                  <Loader2 v-if="toggling === alert.id" :size="16" class="spinner" />
                  <PowerOff v-else :size="18" />
                </button>
                <button
                  @click="deleteAlert(alert.id)"
                  :disabled="deleting === alert.id"
                  class="delete-button"
                  title="Remover"
                >
                  <Loader2 v-if="deleting === alert.id" :size="16" class="spinner" />
                  <Trash2 v-else :size="18" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Inactive Alerts -->
        <div v-if="inactiveAlerts.length > 0" class="alerts-section">
          <h2 class="section-title">
            <PowerOff :size="24" />
            <span>Alertas Inativos</span>
            <span class="badge">{{ inactiveAlerts.length }}</span>
          </h2>
          <div class="alerts-grid">
            <div
              v-for="alert in inactiveAlerts"
              :key="alert.id"
              class="alert-card inactive"
            >
              <div class="alert-header">
                <div class="alert-info">
                  <h3 class="alert-ticker">{{ alert.ticker }}</h3>
                  <span class="alert-meta">
                    {{ formatIndicator(alert.indicator_type) }} • {{ formatCondition(alert.condition) }}
                    <span v-if="alert.threshold_value !== null && alert.threshold_value !== undefined">
                      {{ alert.threshold_value }}
                    </span>
                  </span>
                </div>
                <div class="alert-badge inactive-badge">
                  <PowerOff :size="14" />
                  <span>Inativo</span>
                </div>
              </div>
              <div class="alert-actions">
                <button @click="goToAnalysis(alert.ticker)" class="action-button">
                  <TrendingUp :size="16" />
                  <span>Ver Análise</span>
                </button>
                <button
                  @click="toggleAlert(alert.id)"
                  :disabled="toggling === alert.id"
                  class="toggle-button"
                  title="Ativar"
                >
                  <Loader2 v-if="toggling === alert.id" :size="16" class="spinner" />
                  <Power v-else :size="18" />
                </button>
                <button
                  @click="deleteAlert(alert.id)"
                  :disabled="deleting === alert.id"
                  class="delete-button"
                  title="Remover"
                >
                  <Loader2 v-if="deleting === alert.id" :size="16" class="spinner" />
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
@import '../styles/alerts.css';
</style>

