<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Coins, ArrowLeft, BarChart, Target, Activity } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function goToHome() {
  router.push('/')
}

async function handleSubmit() {
  error.value = ''
  
  if (!email.value || !password.value) {
    error.value = 'Por favor, preencha todos os campos'
    return
  }

  loading.value = true
  try {
    await authStore.login({
      email: email.value,
      password: password.value,
    })
    router.push('/home')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Erro ao fazer login'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <button @click="goToHome" class="back-button" title="Voltar para a página inicial">
      <ArrowLeft :size="20" />
      <span>Voltar</span>
    </button>
    <div class="login-wrapper">
      <div class="login-left">
        <div class="left-content">
          <div class="logo">
            <Coins :size="64" />
          </div>
          <h1>Bem-vindo de volta</h1>
          <p>Acesse seu portfólio, alertas e análises técnicas em tempo real</p>
          <div class="features">
            <div class="feature-item">
              <span class="feature-icon">
                <BarChart :size="16" />
              </span>
              <span>Portfólio com P&L atualizado</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">
                <Target :size="16" />
              </span>
              <span>Alertas por indicadores técnicos</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">
                <Activity :size="16" />
              </span>
              <span>Scanner e análise técnica completa</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-card">
          <div class="login-header">
            <h2>Entrar</h2>
            <p>Acesse sua conta e continue gerenciando seus investimentos</p>
          </div>

          <form @submit.prevent="handleSubmit" class="login-form">
            <div v-if="error" class="error-message">
              {{ error }}
            </div>

            <div class="form-group">
              <label for="email">E-mail</label>
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
              <label for="password">Senha</label>
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="••••••••"
                required
                autocomplete="current-password"
              />
            </div>

            <button type="submit" :disabled="loading" class="submit-button">
              {{ loading ? 'Entrando...' : 'Entrar' }}
            </button>
          </form>

          <div class="login-footer">
            <p>
              Não tem uma conta?
              <router-link to="/register" class="link">Crie uma aqui</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/login.css';
</style>