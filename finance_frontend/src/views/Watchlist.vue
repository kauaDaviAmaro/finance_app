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
@import '../styles/watchlist.css';
</style>

