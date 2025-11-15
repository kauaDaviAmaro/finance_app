<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api, type User, type UserUpdate, type ChangePasswordRequest, ApiError } from '../services/api'
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
  return dateStr ? new Date(dateStr).toLocaleDateString() : '-'
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
  } catch (err) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Erro ao alterar senha'
  } finally {
    changingPassword.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <Navbar />
    <div class="profile-container">
    <h1 class="page-title">Perfil</h1>

    <div v-if="errorMessage" class="alert error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert success">{{ successMessage }}</div>

    <!-- Basic Info -->
    <section class="profile-card">
      <div class="card-header">
        <h2>Informações Básicas</h2>
      </div>
      <div class="form-grid">
        <label class="form-field">
          <span class="label">Email</span>
          <input
            v-model="profileForm.email"
            type="email"
            class="input"
            :disabled="loading || saving"
          />
        </label>

        <label class="form-field">
          <span class="label">Username</span>
          <input
            v-model="profileForm.username"
            type="text"
            class="input"
            :disabled="loading || saving"
          />
        </label>

        <div class="meta">Membro desde: <strong>{{ memberSince }}</strong></div>

        <div class="actions">
          <button class="btn primary" :disabled="saving || loading" @click="saveProfile">
            {{ saving ? 'Salvando...' : 'Salvar' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Security -->
    <section class="profile-card">
      <div class="card-header">
        <h2>Segurança</h2>
      </div>
      <div class="form-grid">
        <label class="form-field">
          <span class="label">Senha atual</span>
          <input
            v-model="passwordForm.current_password"
            type="password"
            class="input"
            :disabled="changingPassword"
          />
        </label>

        <label class="form-field">
          <span class="label">Nova senha</span>
          <input
            v-model="passwordForm.new_password"
            type="password"
            class="input"
            :disabled="changingPassword"
          />
        </label>

        <div class="actions">
          <button class="btn primary" :disabled="changingPassword" @click="changePassword">
            {{ changingPassword ? 'Alterando...' : 'Alterar senha' }}
          </button>
        </div>

        <div class="meta">
          2FA: <strong>{{ (auth.user?.two_factor_enabled ?? false) ? 'Ativado' : 'Desativado' }}</strong>
        </div>
      </div>
    </section>

    <!-- Billing / Subscription -->
    <section class="profile-card">
      <div class="card-header">
        <h2>Assinatura</h2>
      </div>
      <div v-if="!subscription" class="loading">Carregando...</div>
      <div v-else class="subscription-info">
        <div class="meta">
          Status: <strong>{{ subscription.subscription_status ?? 'inactive' }}</strong>
        </div>
        <div class="meta">
          Plano: <strong>{{ subscription.is_pro ? 'PRO' : 'FREE' }}</strong>
        </div>
        <div class="actions">
          <router-link to="/subscription" class="btn secondary">Gerenciar Assinatura</router-link>
        </div>
      </div>
    </section>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.alert {
  padding: 10px 12px;
  border-radius: 8px;
  margin: 0 0 16px 0;
  font-size: 14px;
}
.alert.error { background: #fee2e2; color: #991b1b; }
.alert.success { background: #dcfce7; color: #14532d; }

.profile-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f1f5f9;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.form-field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 14px; color: #64748b; font-weight: 500; }
.input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
}
.input:disabled { background: #f8fafc; cursor: not-allowed; }

.meta { font-size: 14px; color: #374151; }

.actions { display: flex; gap: 12px; margin-top: 4px; }
.btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.btn.primary { background: #3b82f6; color: white; }
.btn.primary:hover { filter: brightness(0.95); }
.btn.primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn.secondary { background: #4f46e5; color: white; }
.btn.secondary:hover { filter: brightness(0.95); }

.loading { color: #64748b; font-size: 14px; }

.subscription-info { display: flex; flex-direction: column; gap: 8px; }

@media (max-width: 640px) {
  .profile-container { padding: 16px 12px; }
}
</style>


