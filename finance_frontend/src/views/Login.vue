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
.login-container {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
}

.back-button {
  position: absolute;
  top: 20px;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

.back-button:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #3b82f6;
  transform: translateX(-2px);
}

.login-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  background: white;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  min-height: 600px;
}

.login-left {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  padding: 60px 50px;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.3;
  animation: gridMove 20s linear infinite;
}

.login-left::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  animation: pulse 4s ease-in-out infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.3;
  }
}

.left-content {
  position: relative;
  z-index: 1;
}

.logo {
  margin-bottom: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  animation: float 3s ease-in-out infinite;
  color: white;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.login-left h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 16px 0;
  line-height: 1.2;
}

.login-left p {
  font-size: 16px;
  opacity: 1;
  line-height: 1.6;
  margin-bottom: 40px;
  color: rgba(255, 255, 255, 0.98);
}

.features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
}

.feature-icon {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
  color: white;
  transition: all 0.3s ease;
}

.feature-item:hover .feature-icon {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1) rotate(5deg);
}

.login-right {
  padding: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 420px;
}

.login-header {
  margin-bottom: 32px;
}

.login-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.login-header p {
  color: #475569;
  font-size: 14px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
  border: 1px solid #fecaca;
  font-weight: 500;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input {
  padding: 12px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s;
  background: #f8fafc;
  color: #0f172a;
}

.form-group input:hover {
  border-color: #cbd5e1;
  background: white;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.submit-button {
  padding: 14px 24px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 8px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.login-footer {
  margin-top: 28px;
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.login-footer p {
  color: #475569;
  font-size: 14px;
  margin: 0;
}

.link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
  margin-left: 4px;
}

.link:hover {
  color: #0ea5e9;
}

@media (max-width: 968px) {
  .login-wrapper {
    grid-template-columns: 1fr;
    max-width: 600px;
  }

  .login-left {
    display: none;
  }

  .login-right {
    padding: 40px 30px;
  }
}

@media (max-width: 640px) {
  .login-container {
    padding: 0;
  }

  .back-button {
    top: 12px;
    left: 12px;
    padding: 8px 12px;
    font-size: 13px;
  }

  .back-button span {
    display: none;
  }

  .login-wrapper {
    border-radius: 0;
    min-height: 100vh;
  }

  .login-right {
    padding: 30px 20px;
  }

  .login-header h2 {
    font-size: 24px;
  }
}
</style>