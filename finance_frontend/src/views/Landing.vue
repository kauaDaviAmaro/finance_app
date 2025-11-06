<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Coins, BarChart, Eye, Bell, TrendingUp, Shield, Zap, ArrowRight } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

function goToLogin() {
  router.push('/login')
}

function goToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="landing-container">
    <header class="landing-header">
      <div class="header-content">
        <div class="header-left">
          <Coins :size="32" class="logo-icon" />
          <h1>Finance App</h1>
        </div>
        <div class="header-actions">
          <button @click="goToLogin" class="header-btn login-btn">
            Entrar
          </button>
          <button @click="goToRegister" class="header-btn register-btn">
            Criar conta
          </button>
        </div>
      </div>
    </header>

    <main class="landing-main">
      <section class="hero-section">
        <div class="hero-content">
          <h2 class="hero-title">
            Gerencie seus investimentos com
            <span class="gradient-text">inteligência</span>
          </h2>
          <p class="hero-subtitle">
            Plataforma completa para acompanhar seu portfólio, monitorar ações e receber alertas personalizados sobre o mercado financeiro.
          </p>
          <div class="hero-actions">
            <button @click="goToRegister" class="cta-button primary">
              Começar agora
              <ArrowRight :size="20" />
            </button>
            <button @click="goToLogin" class="cta-button secondary">
              Já tenho conta
            </button>
          </div>
        </div>
      </section>

      <section class="features-section">
        <div class="features-header">
          <h3>Tudo que você precisa em um só lugar</h3>
          <p>Ferramentas poderosas para gerenciar seus investimentos</p>
        </div>

        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <BarChart :size="32" class="feature-icon" />
            </div>
            <h4>Portfólio</h4>
            <p>Acompanhe todos os seus investimentos em um painel centralizado. Calcule ganhos, perdas e performance em tempo real.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <Eye :size="32" class="feature-icon" />
            </div>
            <h4>Lista de Observação</h4>
            <p>Monitore ações e ativos que você deseja acompanhar. Receba atualizações sobre os movimentos do mercado.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <Bell :size="32" class="feature-icon" />
            </div>
            <h4>Alertas Inteligentes</h4>
            <p>Configure alertas personalizados para preços, variações e condições específicas do mercado.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <TrendingUp :size="32" class="feature-icon" />
            </div>
            <h4>Análise de Mercado</h4>
            <p>Visualize dados históricos, gráficos e tendências para tomar decisões informadas.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <Shield :size="32" class="feature-icon" />
            </div>
            <h4>Segurança</h4>
            <p>Seus dados estão protegidos com criptografia e seguimos as melhores práticas de segurança.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <Zap :size="32" class="feature-icon" />
            </div>
            <h4>Performance</h4>
            <p>Interface rápida e responsiva, atualizações em tempo real e experiência otimizada.</p>
          </div>
        </div>
      </section>

      <section class="cta-section">
        <div class="cta-content">
          <h3>Pronto para começar?</h3>
          <p>Crie sua conta gratuitamente e comece a gerenciar seus investimentos hoje mesmo.</p>
          <button @click="goToRegister" class="cta-button primary large">
            Criar conta gratuita
            <ArrowRight :size="20" />
          </button>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <div class="footer-content">
        <p>&copy; 2024 Finance App. Todos os direitos reservados.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.landing-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  color: #3b82f6;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.login-btn {
  background: transparent;
  color: #475569;
}

.login-btn:hover {
  color: #3b82f6;
  background: #f1f5f9;
}

.register-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.landing-main {
  flex: 1;
}

.hero-section {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  padding: 100px 20px;
  text-align: center;
  color: white;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 24px 0;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 20px;
  opacity: 0.95;
  margin: 0 0 40px 0;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.98);
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.cta-button.primary {
  background: white;
  color: #3b82f6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cta-button.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.cta-button.primary.large {
  padding: 16px 32px;
  font-size: 18px;
}

.cta-button.secondary {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
}

.cta-button.secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
}

.features-section {
  padding: 80px 20px;
  background: #f8fafc;
}

.features-header {
  text-align: center;
  max-width: 600px;
  margin: 0 auto 60px;
}

.features-header h3 {
  font-size: 36px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.features-header p {
  font-size: 18px;
  color: #64748b;
  margin: 0;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.feature-card {
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon-wrapper {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.feature-icon {
  color: white;
}

.feature-card h4 {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.feature-card p {
  color: #64748b;
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.cta-section {
  padding: 80px 20px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  text-align: center;
  color: white;
}

.cta-content {
  max-width: 600px;
  margin: 0 auto;
}

.cta-content h3 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.cta-content p {
  font-size: 18px;
  opacity: 0.95;
  margin: 0 0 32px 0;
  color: rgba(255, 255, 255, 0.98);
}

.landing-footer {
  background: #0f172a;
  color: #94a3b8;
  padding: 40px 20px;
  text-align: center;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-content p {
  margin: 0;
  font-size: 14px;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .header-actions {
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .header-btn {
    width: 100%;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    flex-direction: column;
  }

  .cta-button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .hero-section {
    padding: 60px 20px;
  }

  .hero-title {
    font-size: 28px;
  }

  .features-section {
    padding: 60px 20px;
  }

  .features-header h3 {
    font-size: 28px;
  }
}
</style>
