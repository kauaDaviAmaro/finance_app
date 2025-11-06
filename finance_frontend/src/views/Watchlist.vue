<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError, type WatchlistResponse, type WatchlistItem } from '../services/api/index'
import { Eye, Plus, Trash2, Loader2, AlertCircle, Search, X } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()

const watchlist = ref<WatchlistResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const adding = ref(false)
const removing = ref<string | null>(null)
const newTicker = ref('')
const showAddForm = ref(false)

async function loadWatchlist() {
  loading.value = true
  error.value = null
  try {
    watchlist.value = await api.getWatchlist()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao carregar watchlist. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function addTicker() {
  if (!newTicker.value.trim()) {
    error.value = 'Por favor, digite um ticker'
    return
  }

  adding.value = true
  error.value = null

  try {
    await api.addToWatchlist(newTicker.value.toUpperCase().trim())
    newTicker.value = ''
    showAddForm.value = false
    await loadWatchlist()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao adicionar ticker. Tente novamente.'
    }
    console.error(err)
  } finally {
    adding.value = false
  }
}

async function removeTicker(ticker: string) {
  if (!confirm(`Deseja remover ${ticker} da sua watchlist?`)) {
    return
  }

  removing.value = ticker
  error.value = null

  try {
    await api.removeFromWatchlist(ticker)
    await loadWatchlist()
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao remover ticker. Tente novamente.'
    }
    console.error(err)
  } finally {
    removing.value = null
  }
}

function goToAnalysis(ticker: string) {
  router.push(`/market-analysis?ticker=${ticker}`)
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

  await loadWatchlist()
})
</script>

<template>
  <div class="watchlist-container">
    <Navbar />

    <main class="watchlist-main">
      <div class="header-section">
        <div class="header-content">
          <div class="title-group">
            <Eye :size="32" class="title-icon" />
            <div>
              <h1>Minha Watchlist</h1>
              <p class="subtitle">Monitore seus ativos favoritos</p>
            </div>
          </div>
          <button @click="showAddForm = !showAddForm" class="add-button">
            <Plus :size="20" />
            <span>Adicionar Ticker</span>
          </button>
        </div>
      </div>

      <!-- Add Form -->
      <div v-if="showAddForm" class="add-form-card">
        <div class="form-header">
          <h3>Adicionar à Watchlist</h3>
          <button @click="showAddForm = false" class="close-button">
            <X :size="20" />
          </button>
        </div>
        <div class="form-content">
          <div class="input-group">
            <label for="new-ticker">Ticker</label>
            <div class="input-wrapper">
              <Search :size="20" class="input-icon" />
              <input
                id="new-ticker"
                v-model="newTicker"
                type="text"
                placeholder="Ex: PETR4, AAPL, MSFT"
                @keyup.enter="addTicker"
                :disabled="adding"
              />
            </div>
          </div>
          <div class="form-actions">
            <button @click="addTicker" :disabled="adding || !newTicker.trim()" class="submit-button">
              <Loader2 v-if="adding" :size="16" class="spinner" />
              <span>{{ adding ? 'Adicionando...' : 'Adicionar' }}</span>
            </button>
            <button @click="showAddForm = false" :disabled="adding" class="cancel-button">
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
        <p>Carregando watchlist...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!watchlist || watchlist.items.length === 0" class="empty-state">
        <Eye :size="64" class="empty-icon" />
        <h2>Sua watchlist está vazia</h2>
        <p>Adicione tickers para começar a monitorar seus ativos favoritos</p>
        <button @click="showAddForm = true" class="empty-action-button">
          <Plus :size="20" />
          <span>Adicionar Primeiro Ticker</span>
        </button>
      </div>

      <!-- Watchlist Items -->
      <div v-else class="watchlist-grid">
        <div
          v-for="item in watchlist.items"
          :key="item.id"
          class="watchlist-card"
        >
          <div class="card-header">
            <div class="ticker-info">
              <h3 class="ticker-symbol">{{ item.ticker }}</h3>
              <span class="added-date">
                Adicionado em {{ new Date(item.created_at).toLocaleDateString('pt-BR') }}
              </span>
            </div>
            <button
              @click="removeTicker(item.ticker)"
              :disabled="removing === item.ticker"
              class="remove-button"
              title="Remover da watchlist"
            >
              <Loader2 v-if="removing === item.ticker" :size="16" class="spinner" />
              <Trash2 v-else :size="18" />
            </button>
          </div>
          <div class="card-actions">
            <button @click="goToAnalysis(item.ticker)" class="action-button">
              <Search :size="16" />
              <span>Ver Análise</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.watchlist-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
}

.watchlist-main {
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

.input-wrapper input {
  width: 100%;
  padding: 12px 12px 12px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-wrapper input:disabled {
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

/* Watchlist Grid */
.watchlist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.watchlist-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.watchlist-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.ticker-info {
  flex: 1;
}

.ticker-symbol {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.added-date {
  font-size: 12px;
  color: #64748b;
}

.remove-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-button:hover:not(:disabled) {
  background: #fecaca;
  transform: scale(1.05);
}

.remove-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 8px;
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

@media (max-width: 768px) {
  .watchlist-main {
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

  .watchlist-grid {
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
}
</style>

