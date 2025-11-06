<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type AlertListResponse, type Alert, type AlertCreate } from '../services/api'
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
      error.value = err.message
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
          <button @click="showAddForm = !showAddForm" class="add-button">
            <Plus :size="20" />
            <span>Novo Alerta</span>
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
        <button @click="showAddForm = true" class="empty-action-button">
          <Plus :size="20" />
          <span>Criar Primeiro Alerta</span>
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
.alerts-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
}

.alerts-main {
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

.stat-card.active {
  border: 2px solid #10b981;
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

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
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
.input-group select,
.input-group input {
  width: 100%;
  padding: 12px 12px 12px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s;
}

.input-group select,
.input-group input[type="number"] {
  padding-left: 12px;
}

.input-wrapper input:focus,
.input-group select:focus,
.input-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-wrapper input:disabled,
.input-group select:disabled,
.input-group input:disabled {
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

/* Alerts Content */
.alerts-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.alerts-section {
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

.alerts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.alert-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.alert-card.active {
  border-left: 4px solid #10b981;
}

.alert-card.inactive {
  border-left: 4px solid #64748b;
  opacity: 0.8;
}

.alert-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}

.alert-info {
  flex: 1;
}

.alert-ticker {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.alert-meta {
  font-size: 13px;
  color: #64748b;
  display: block;
}

.alert-badge {
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

.inactive-badge {
  background: #f1f5f9;
  color: #64748b;
}

.triggered-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #fef3c7;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #92400e;
}

.alert-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-button {
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

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.toggle-button,
.delete-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-button {
  background: #f1f5f9;
  color: #64748b;
}

.toggle-button:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}

.delete-button {
  background: #fee2e2;
  color: #dc2626;
}

.delete-button:hover:not(:disabled) {
  background: #fecaca;
  transform: scale(1.05);
}

.toggle-button:disabled,
.delete-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .alerts-main {
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

  .alerts-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .title-group h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }

  .alert-actions {
    flex-wrap: wrap;
  }

  .action-button {
    width: 100%;
    justify-content: center;
  }
}
</style>

