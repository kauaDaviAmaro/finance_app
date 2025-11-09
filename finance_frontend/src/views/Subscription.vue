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
.subscription-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
}

.subscription-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
}

.header-section {
  margin-bottom: 48px;
  text-align: center;
}

.header-content {
  color: white;
}

.crown-icon {
  margin-bottom: 16px;
  color: #fbbf24;
}

.header-content h1 {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: white;
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
  color: rgba(255, 255, 255, 0.95);
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #d1fae5;
  color: #065f46;
  border-radius: 12px;
  margin-bottom: 24px;
  border-left: 4px solid #10b981;
}

.success-banner span {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

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

.pricing-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 32px;
}

.pricing-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.pricing-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #f1f5f9;
}

.pricing-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.pricing-amount {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.currency {
  font-size: 20px;
  font-weight: 600;
  color: #64748b;
}

.amount {
  font-size: 48px;
  font-weight: 700;
  color: #0f172a;
}

.period {
  font-size: 18px;
  color: #64748b;
  margin-left: 4px;
}

.features-list {
  margin-bottom: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  font-size: 16px;
  color: #0f172a;
}

.check-icon {
  color: #10b981;
  flex-shrink: 0;
}

.pricing-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subscribe-button,
.manage-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.subscribe-button {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
}

.subscribe-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(251, 191, 36, 0.4);
}

.manage-button {
  background: #f1f5f9;
  color: #0f172a;
}

.manage-button:hover:not(:disabled) {
  background: #e2e8f0;
}

.subscribe-button:disabled,
.manage-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.comparison-section {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.comparison-section h3 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 24px 0;
}

.comparison-table {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1px;
  background: #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.comparison-row {
  display: contents;
}

.comparison-feature,
.comparison-plan {
  padding: 16px;
  background: white;
  font-size: 14px;
}

.comparison-feature {
  font-weight: 600;
  color: #0f172a;
}

.comparison-plan {
  text-align: center;
  color: #64748b;
}

.comparison-plan.pro {
  background: #fef3c7;
  color: #92400e;
  font-weight: 600;
}

@media (max-width: 968px) {
  .pricing-section {
    grid-template-columns: 1fr;
  }

  .header-content h1 {
    font-size: 36px;
  }
}

@media (max-width: 640px) {
  .subscription-main {
    padding: 40px 16px;
  }

  .header-content h1 {
    font-size: 28px;
  }

  .pricing-card,
  .comparison-section {
    padding: 24px;
  }

  .comparison-table {
    font-size: 12px;
  }

  .comparison-feature,
  .comparison-plan {
    padding: 12px;
  }
}
</style>



