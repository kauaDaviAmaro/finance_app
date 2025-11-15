<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api, type User, type UserUpdate, type ChangePasswordRequest, ApiError } from '../services/api'
import { User as UserIcon, Mail, Lock, Shield, CreditCard, CheckCircle, X, Loader2, Calendar, Crown } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)

const profileForm = ref<UserUpdate>({
  email: undefined,
  username: undefined,
})

const passwordForm = ref<ChangePasswordRequest>({
  current_password: '',
  new_password: '',
})

const subscription = ref<{ is_pro: boolean; subscription_status: string | null; role: User['role'] } | null>(null)

const memberSince = computed(() => {
  const dateStr = (auth.user?.created_at as string | undefined)
  return dateStr ? new Date(dateStr).toLocaleDateString('pt-BR', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  }) : '-'
})

const subscriptionStatusLabel = computed(() => {
  if (!subscription.value) return 'Carregando...'
  const status = subscription.value.subscription_status
  if (status === 'active') return 'Ativa'
  if (status === 'canceled') return 'Cancelada'
  if (status === 'past_due') return 'Vencida'
  return 'Inativa'
})

const subscriptionStatusColor = computed(() => {
  if (!subscription.value) return 'gray'
  const status = subscription.value.subscription_status
  if (status === 'active') return 'green'
  if (status === 'canceled') return 'red'
  if (status === 'past_due') return 'yellow'
  return 'gray'
})

async function load() {
  loading.value = true
  errorMessage.value = null
  try {
    if (!auth.user) {
      await auth.fetchUser()
    }
    profileForm.value.email = auth.user?.email
    profileForm.value.username = auth.user?.username
    subscription.value = await api.getSubscriptionStatus()
  } catch (err) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Erro ao carregar perfil'
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  errorMessage.value = null
  successMessage.value = null
  try {
    await api.updateMe({
      email: profileForm.value.email,
      username: profileForm.value.username,
    })
    await auth.fetchUser()
    successMessage.value = 'Perfil atualizado com sucesso'
    setTimeout(() => {
      successMessage.value = null
    }, 5000)
  } catch (err) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Erro ao atualizar perfil'
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  changingPassword.value = true
  errorMessage.value = null
  successMessage.value = null
  try {
    await api.changePassword({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
    })
    passwordForm.value.current_password = ''
    passwordForm.value.new_password = ''
    successMessage.value = 'Senha alterada com sucesso'
    setTimeout(() => {
      successMessage.value = null
    }, 5000)
  } catch (err) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Erro ao alterar senha'
  } finally {
    changingPassword.value = false
  }
}

function dismissError() {
  errorMessage.value = null
}

function dismissSuccess() {
  successMessage.value = null
}

onMounted(load)
</script>

<template>
  <div class="profile-container">
    <Navbar />
    
    <main class="profile-main">
      <div class="header-section">
        <div class="header-content">
          <div class="avatar-wrapper">
            <UserIcon :size="48" class="avatar-icon" />
          </div>
          <h1>{{ auth.user?.username || 'Perfil' }}</h1>
          <p class="subtitle">Gerencie suas informações pessoais e configurações de conta</p>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="alert-banner success">
        <CheckCircle :size="20" />
        <span>{{ successMessage }}</span>
        <button @click="dismissSuccess" class="alert-close">
          <X :size="16" />
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="alert-banner error">
        <X :size="20" />
        <span>{{ errorMessage }}</span>
        <button @click="dismissError" class="alert-close">
          <X :size="16" />
        </button>
      </div>

      <div v-if="loading" class="loading-container">
        <Loader2 :size="48" class="spinner" />
        <p>Carregando perfil...</p>
      </div>

      <div v-else class="profile-content">
        <!-- Basic Info -->
        <section class="profile-card">
          <div class="card-header">
            <UserIcon :size="24" class="header-icon" />
            <h2>Informações Básicas</h2>
          </div>
          <div class="card-body">
            <div class="form-grid">
              <label class="form-field">
                <div class="field-label">
                  <Mail :size="18" class="field-icon" />
                  <span class="label">Email</span>
                </div>
                <input
                  v-model="profileForm.email"
                  type="email"
                  class="input"
                  placeholder="seu@email.com"
                  :disabled="loading || saving"
                />
              </label>

              <label class="form-field">
                <div class="field-label">
                  <UserIcon :size="18" class="field-icon" />
                  <span class="label">Username</span>
                </div>
                <input
                  v-model="profileForm.username"
                  type="text"
                  class="input"
                  placeholder="seu_username"
                  :disabled="loading || saving"
                />
              </label>

              <div class="info-item">
                <Calendar :size="18" class="info-icon" />
                <div class="info-content">
                  <span class="info-label">Membro desde</span>
                  <span class="info-value">{{ memberSince }}</span>
                </div>
              </div>

              <div class="actions">
                <button class="btn primary" :disabled="saving || loading" @click="saveProfile">
                  <Loader2 v-if="saving" :size="18" class="btn-spinner" />
                  <span>{{ saving ? 'Salvando...' : 'Salvar Alterações' }}</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Security -->
        <section class="profile-card">
          <div class="card-header">
            <Shield :size="24" class="header-icon" />
            <h2>Segurança</h2>
          </div>
          <div class="card-body">
            <div class="form-grid">
              <label class="form-field">
                <div class="field-label">
                  <Lock :size="18" class="field-icon" />
                  <span class="label">Senha atual</span>
                </div>
                <input
                  v-model="passwordForm.current_password"
                  type="password"
                  class="input"
                  placeholder="••••••••"
                  :disabled="changingPassword"
                />
              </label>

              <label class="form-field">
                <div class="field-label">
                  <Lock :size="18" class="field-icon" />
                  <span class="label">Nova senha</span>
                </div>
                <input
                  v-model="passwordForm.new_password"
                  type="password"
                  class="input"
                  placeholder="••••••••"
                  :disabled="changingPassword"
                />
              </label>

              <div class="actions">
                <button class="btn primary" :disabled="changingPassword" @click="changePassword">
                  <Loader2 v-if="changingPassword" :size="18" class="btn-spinner" />
                  <span>{{ changingPassword ? 'Alterando...' : 'Alterar Senha' }}</span>
                </button>
              </div>

              <div class="info-item">
                <Shield :size="18" class="info-icon" />
                <div class="info-content">
                  <span class="info-label">Autenticação de dois fatores</span>
                  <span :class="['status-badge', (auth.user?.two_factor_enabled ?? false) ? 'enabled' : 'disabled']">
                    {{ (auth.user?.two_factor_enabled ?? false) ? 'Ativado' : 'Desativado' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Subscription -->
        <section class="profile-card">
          <div class="card-header">
            <CreditCard :size="24" class="header-icon" />
            <h2>Assinatura</h2>
          </div>
          <div class="card-body">
            <div v-if="!subscription" class="loading-state">
              <Loader2 :size="24" class="spinner" />
              <span>Carregando informações...</span>
            </div>
            <div v-else class="subscription-info">
              <div class="subscription-grid">
                <div class="info-item">
                  <Crown :size="18" class="info-icon" />
                  <div class="info-content">
                    <span class="info-label">Plano</span>
                    <span :class="['plan-badge', subscription.is_pro ? 'pro' : 'free']">
                      {{ subscription.is_pro ? 'PRO' : 'FREE' }}
                    </span>
                  </div>
                </div>

                <div class="info-item">
                  <CheckCircle :size="18" class="info-icon" />
                  <div class="info-content">
                    <span class="info-label">Status</span>
                    <span :class="['status-badge', subscriptionStatusColor]">
                      {{ subscriptionStatusLabel }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="actions">
                <router-link to="/subscription" class="btn secondary">
                  <CreditCard :size="18" />
                  <span>Gerenciar Assinatura</span>
                </router-link>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/profile.css';
</style>


