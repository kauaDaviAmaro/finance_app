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
@import '../styles/landing.css';
</style>
