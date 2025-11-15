<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Coins, ArrowLeft, Search, LineChart, BarChart } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

function validateForm(): boolean {
  if (!email.value || !username.value || !password.value) {
    error.value = 'Por favor, preencha todos os campos obrigatórios'
    return false
  }

  if (username.value.length < 3) {
    error.value = 'O nome de usuário deve ter pelo menos 3 caracteres'
    return false
  }

  if (password.value.length < 6) {
    error.value = 'A senha deve ter pelo menos 6 caracteres'
    return false
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'As senhas não coincidem'
    return false
  }

  return true
}

function goToHome() {
  router.push('/')
}

async function handleSubmit() {
  error.value = ''

  if (!validateForm()) {
    return
  }

  loading.value = true
  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password: password.value,
    })
    router.push('/home')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Erro ao criar conta'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <button @click="goToHome" class="back-button" title="Voltar para a página inicial">
      <ArrowLeft :size="20" />
      <span>Voltar</span>
    </button>
    <div class="register-wrapper">
      <div class="register-left">
        <div class="left-content">
          <div class="logo">
            <Coins :size="64" />
          </div>
          <h1>Comece sua jornada financeira</h1>
          <p>Crie sua conta e tenha acesso a scanner de ações, análise técnica e gestão de portfólio profissional</p>
          <div class="features">
            <div class="feature-item">
              <span class="feature-icon">
                <Search :size="16" />
              </span>
              <span>Scanner PRO com filtros por RSI, MACD e Bollinger</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">
                <LineChart :size="16" />
              </span>
              <span>Análise técnica com 6+ indicadores</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">
                <BarChart :size="16" />
              </span>
              <span>Portfólio com cálculo automático de P&L</span>
            </div>
          </div>
        </div>
      </div>

      <div class="register-right">
        <div class="register-card">
          <div class="register-header">
            <h2>Criar conta</h2>
            <p>Comece a usar scanner, análise técnica e gestão de portfólio</p>
          </div>

          <form @submit.prevent="handleSubmit" class="register-form">
            <div v-if="error" class="error-message">
              {{ error }}
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="email">E-mail *</label>
                <input
                  id="email"
                  v-model="email"
                  type="email"
                  placeholder="seu@email.com"
                  required
                  autocomplete="email"
                />
              </div>

              <div class="form-group">
                <label for="username">Nome de usuário *</label>
                <input
                  id="username"
                  v-model="username"
                  type="text"
                  placeholder="seu_usuario"
                  required
                  minlength="3"
                  autocomplete="username"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="password">Senha *</label>
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  placeholder="••••••••"
                  required
                  minlength="6"
                  autocomplete="new-password"
                />
                <small>Mín. 6 caracteres</small>
              </div>

              <div class="form-group">
                <label for="confirmPassword">Confirmar senha *</label>
                <input
                  id="confirmPassword"
                  v-model="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  required
                  autocomplete="new-password"
                />
              </div>
            </div>

            <button type="submit" :disabled="loading" class="submit-button">
              {{ loading ? 'Criando conta...' : 'Criar conta' }}
            </button>
          </form>

          <div class="register-footer">
            <p>
              Já tem uma conta?
              <router-link to="/login" class="link">Faça login</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/register.css';
</style>