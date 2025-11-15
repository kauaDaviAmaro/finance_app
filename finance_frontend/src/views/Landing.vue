<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Coins, BarChart, Eye, ArrowRight, Search, Activity, Target, LineChart } from 'lucide-vue-next'

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
          <Coins class="logo-icon" />
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
        <div class="hero-background">
          <div class="hero-grid"></div>
          <div class="hero-blob blob-1"></div>
          <div class="hero-blob blob-2"></div>
        </div>
        <div class="hero-content">
          <div class="hero-badge">
            <Activity :size="14" />
            <span>Plataforma profissional para traders</span>
          </div>
          <h2 class="hero-title">
            Scanner de ações, análise técnica e
            <span class="gradient-text">gestão de portfólio</span>
            em uma plataforma
          </h2>
          <p class="hero-subtitle">
            Filtre ações por RSI, MACD e Bollinger Bands. Analise gráficos com 6+ indicadores técnicos. Configure alertas automáticos. Calcule P&L do seu portfólio em tempo real.
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
          <div class="hero-stats">
            <div class="stat-item">
              <div class="stat-value">6+</div>
              <div class="stat-label">Indicadores técnicos</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">100+</div>
              <div class="stat-label">Ações escaneadas</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">5 anos</div>
              <div class="stat-label">Dados históricos</div>
            </div>
          </div>
        </div>
      </section>

      <section class="features-section">
        <div class="features-header">
          <h3>Funcionalidades que fazem a diferença</h3>
          <p>Ferramentas profissionais para traders e investidores</p>
        </div>

        <div class="features-grid">
          <div class="feature-card feature-card-pro">
            <div class="feature-badge">PRO</div>
            <div class="feature-icon-wrapper feature-icon-gradient-1">
              <Search :size="32" class="feature-icon" />
            </div>
            <h4>Scanner de Ações (PRO)</h4>
            <p>Filtre centenas de ações por indicadores técnicos: RSI abaixo de 30 (sobrevenda), MACD positivo, toque nas Bollinger Bands. Encontre oportunidades rapidamente.</p>
            <div class="feature-tags">
              <span class="tag">RSI</span>
              <span class="tag">MACD</span>
              <span class="tag">Bollinger</span>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper feature-icon-gradient-2">
              <LineChart :size="32" class="feature-icon" />
            </div>
            <h4>Análise Técnica Completa</h4>
            <p>RSI, MACD, Stochastic, Bollinger Bands, ATR e OBV. Gráficos interativos com dados históricos de até 5 anos. Análise fundamentalista (P/L, P/VP, Beta, Dividend Yield).</p>
            <div class="feature-tags">
              <span class="tag">6+ Indicadores</span>
              <span class="tag">Gráficos</span>
              <span class="tag">Fundamentalista</span>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper feature-icon-gradient-3">
              <Target :size="32" class="feature-icon" />
            </div>
            <h4>Alertas por Indicadores</h4>
            <p>Configure alertas quando RSI cruzar acima de 70, MACD cruzar abaixo de zero, ou preço tocar as Bollinger Bands. Receba notificações por email automaticamente.</p>
            <div class="feature-tags">
              <span class="tag">Email</span>
              <span class="tag">Automático</span>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper feature-icon-gradient-4">
              <BarChart :size="32" class="feature-icon" />
            </div>
            <h4>Portfólio com P&L Real</h4>
            <p>Registre compras e vendas. Cálculo automático de ganhos/perdas realizados e não realizados. Preços atualizados em tempo real via yfinance.</p>
            <div class="feature-tags">
              <span class="tag">P&L</span>
              <span class="tag">Tempo Real</span>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper feature-icon-gradient-5">
              <Eye :size="32" class="feature-icon" />
            </div>
            <h4>Watchlist Personalizada</h4>
            <p>Monitore suas ações favoritas. Acesso rápido à análise técnica e fundamentalista de cada ativo da sua lista.</p>
            <div class="feature-tags">
              <span class="tag">Favoritos</span>
              <span class="tag">Rápido</span>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon-wrapper feature-icon-gradient-6">
              <Activity :size="32" class="feature-icon" />
            </div>
            <h4>Dados em Tempo Real</h4>
            <p>Integração com yfinance para dados de mercado atualizados. Cache inteligente para performance. Processamento assíncrono com Celery.</p>
            <div class="feature-tags">
              <span class="tag">yfinance</span>
              <span class="tag">Cache</span>
              <span class="tag">Celery</span>
            </div>
          </div>
        </div>
      </section>

      <section class="cta-section">
        <div class="cta-content">
          <h3>Comece a usar agora</h3>
          <p>Cadastre-se gratuitamente e tenha acesso a análise técnica, portfólio e watchlist. Upgrade para PRO e desbloqueie o scanner de ações.</p>
          <button @click="goToRegister" class="cta-button primary large">
            Criar conta gratuita
            <ArrowRight :size="20" />
          </button>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-links">
          <div class="footer-column">
            <h5>Plataforma</h5>
            <p>Scanner de ações, análise técnica e gestão de portfólio para traders e investidores.</p>
          </div>
          <div class="footer-column">
            <h5>Recursos</h5>
            <ul>
              <li>Scanner PRO (RSI, MACD, Bollinger)</li>
              <li>Análise técnica (6+ indicadores)</li>
              <li>Alertas automáticos</li>
              <li>Portfólio com P&L</li>
            </ul>
          </div>
          <div class="footer-column">
            <h5>Dados</h5>
            <ul>
              <li>Integração com yfinance</li>
              <li>Dados históricos (até 5 anos)</li>
              <li>Análise fundamentalista</li>
              <li>Atualizações em tempo real</li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2024 Finance App. Todos os direitos reservados.</p>
        </div>
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
  width: 32px;
  height: 32px;
  flex-shrink: 0;
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
  white-space: nowrap;
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
  padding: 120px 20px;
  text-align: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.hero-grid {
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

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.hero-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.2;
  animation: blobFloat 15s ease-in-out infinite;
}

.blob-1 {
  width: 400px;
  height: 400px;
  background: rgba(251, 191, 36, 0.4);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 300px;
  height: 300px;
  background: rgba(139, 92, 246, 0.4);
  bottom: -50px;
  left: -50px;
  animation-delay: 5s;
}

@keyframes blobFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 24px;
  animation: fadeInUp 0.6s ease-out;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-top: 60px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.9);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-content {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 24px 0;
  line-height: 1.2;
  animation: fadeInUp 0.8s ease-out 0.2s both;
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
  animation: fadeInUp 0.8s ease-out 0.4s both;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s ease-out 0.6s both;
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
  padding: 100px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 50%, #ffffff 100%);
  position: relative;
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border: 1px solid transparent;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #0ea5e9, #3b82f6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.1);
}

.feature-card-pro {
  border: 2px solid #fbbf24;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.05), rgba(245, 158, 11, 0.05));
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.2);
}

.feature-card-pro:hover {
  box-shadow: 0 12px 32px rgba(251, 191, 36, 0.3);
  border-color: #f59e0b;
}

.feature-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: white;
  font-size: 12px;
  font-weight: 700;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  transition: all 0.3s ease;
  position: relative;
}

.feature-card:hover .feature-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.feature-icon-gradient-1 {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.feature-icon-gradient-2 {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.feature-icon-gradient-3 {
  background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
}

.feature-icon-gradient-4 {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.feature-icon-gradient-5 {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.feature-icon-gradient-6 {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.feature-icon {
  color: white;
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.tag {
  display: inline-block;
  padding: 4px 12px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  transition: all 0.2s;
}

.feature-card:hover .tag {
  background: #e2e8f0;
  transform: translateY(-2px);
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
  padding: 100px 20px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  text-align: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.cta-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(251, 191, 36, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.cta-content {
  max-width: 600px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
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
  padding: 60px 20px 30px;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 40px;
  margin-bottom: 40px;
}

.footer-column h5 {
  color: white;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.footer-column p {
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  color: #cbd5e1;
}

.footer-column ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-column ul li {
  font-size: 14px;
  line-height: 1.8;
  color: #cbd5e1;
}

.footer-bottom {
  text-align: center;
  padding-top: 30px;
  border-top: 1px solid #1e293b;
}

.footer-bottom p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

@media (max-width: 768px) {
  .landing-header {
    padding: 16px 0;
  }

  .header-content {
    padding: 0 16px;
  }

  .header-left {
    gap: 8px;
  }

  .logo-icon {
    width: 24px;
    height: 24px;
  }

  .header-content h1 {
    font-size: 18px;
  }

  .header-actions {
    gap: 8px;
  }

  .header-btn {
    padding: 8px 16px;
    font-size: 13px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .hero-stats {
    gap: 32px;
  }

  .stat-value {
    font-size: 24px;
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
  .landing-header {
    padding: 12px 0;
  }

  .header-content {
    padding: 0 12px;
  }

  .header-left {
    gap: 6px;
  }

  .logo-icon {
    width: 20px;
    height: 20px;
  }

  .header-content h1 {
    font-size: 16px;
  }

  .header-actions {
    gap: 6px;
  }

  .header-btn {
    padding: 6px 12px;
    font-size: 12px;
  }

  .login-btn {
    display: none;
  }

  .register-btn {
    padding: 8px 16px;
    font-size: 13px;
  }

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

  .footer-links {
    grid-template-columns: 1fr;
    gap: 30px;
  }

  .hero-stats {
    gap: 24px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 12px;
  }
}
</style>
