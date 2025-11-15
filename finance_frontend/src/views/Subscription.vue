<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, ApiError } from '../services/api/index'
import { Crown, Check, Loader2, AlertCircle, X } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const isPro = ref(false)

const features = [
  'Alertas ilimitados',
  'Notificações por email',
  'Portfólio com atualização rápida',
  'Suporte prioritário',
]

async function handleSubscribe() {
  loading.value = true
  error.value = null

  try {
    const session = await api.createCheckoutSession()
    // Redirecionar para o Stripe Checkout
    window.location.href = session.url
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao criar sessão de checkout. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function handleManageSubscription() {
  loading.value = true
  error.value = null

  try {
    const session = await api.createPortalSession()
    // Redirecionar para o Stripe Customer Portal
    window.location.href = session.url
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao acessar portal. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function checkSubscriptionStatus() {
  try {
    const status = await api.getSubscriptionStatus()
    isPro.value = status.is_pro
  } catch (err) {
    console.error('Erro ao verificar status da assinatura:', err)
  }
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

  await checkSubscriptionStatus()

  // Verificar se veio do checkout do Stripe
  if (route.query.session_id) {
    // Atualizar usuário após checkout
    await authStore.fetchUser()
    await checkSubscriptionStatus()
  }
})
</script>

<template>
  <div class="subscription-container">
    <Navbar />

    <main class="subscription-main">
      <div class="header-section">
        <div class="header-content">
          <Crown :size="48" class="crown-icon" />
          <h1>Plano PRO</h1>
          <p class="subtitle">Desbloqueie recursos avançados e monitore o mercado com eficiência</p>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="route.query.session_id && isPro" class="success-banner">
        <Check :size="20" />
        <span>Assinatura ativada com sucesso! Bem-vindo ao Plano PRO!</span>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error-banner">
        <AlertCircle :size="20" />
        <span>{{ error }}</span>
        <button @click="error = null" class="error-close">
          <X :size="16" />
        </button>
      </div>

      <div class="pricing-section">
        <div class="pricing-card">
          <div class="pricing-header">
            <h2>Plano PRO</h2>
            <div class="pricing-amount">
              <span class="currency">R$</span>
              <span class="amount">29,90</span>
              <span class="period">/mês</span>
            </div>
          </div>

          <div class="features-list">
            <div v-for="feature in features" :key="feature" class="feature-item">
              <Check :size="20" class="check-icon" />
              <span>{{ feature }}</span>
            </div>
          </div>

          <div class="pricing-actions">
            <button
              v-if="!isPro"
              @click="handleSubscribe"
              :disabled="loading"
              class="subscribe-button"
            >
              <Loader2 v-if="loading" :size="18" class="spinner" />
              <Crown v-else :size="18" />
              <span>{{ loading ? 'Processando...' : 'Tornar-se PRO' }}</span>
            </button>

            <button
              v-else
              @click="handleManageSubscription"
              :disabled="loading"
              class="manage-button"
            >
              <Loader2 v-if="loading" :size="18" class="spinner" />
              <span>{{ loading ? 'Carregando...' : 'Gerenciar Assinatura' }}</span>
            </button>
          </div>
        </div>

        <div class="comparison-section">
          <h3>Comparação de Planos</h3>
          <div class="comparison-table">
            <div class="comparison-row">
              <div class="comparison-feature">Recurso</div>
              <div class="comparison-plan">Grátis</div>
              <div class="comparison-plan pro">PRO</div>
            </div>
            <div class="comparison-row">
              <div class="comparison-feature">Alertas</div>
              <div class="comparison-plan">1 alerta</div>
              <div class="comparison-plan pro">Ilimitados</div>
            </div>
            <div class="comparison-row">
              <div class="comparison-feature">Notificações por Email</div>
              <div class="comparison-plan">Não</div>
              <div class="comparison-plan pro">Sim</div>
            </div>
            <div class="comparison-row">
              <div class="comparison-feature">Portfólio (Cache)</div>
              <div class="comparison-plan">Lento</div>
              <div class="comparison-plan pro">Rápido</div>
            </div>
            <div class="comparison-row">
              <div class="comparison-feature">Análise Técnica</div>
              <div class="comparison-plan">Sim</div>
              <div class="comparison-plan pro">Sim</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/subscription.css';
</style>





