<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAdminStats, type AdminStats } from '../../services/api/admin.api'
import { Users, Bell, Briefcase, Eye, TrendingUp, BarChart3, Activity } from 'lucide-vue-next'

const stats = ref<AdminStats | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function loadStats() {
  try {
    loading.value = true
    error.value = null
    stats.value = await getAdminStats()
  } catch (err: any) {
    error.value = err.message || 'Erro ao carregar estatísticas'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="admin-dashboard">
    <div class="dashboard-header">
      <h1>Dashboard Administrativo</h1>
      <p class="subtitle">Visão geral do sistema</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner">Carregando...</div>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadStats" class="retry-button">Tentar novamente</button>
    </div>

    <div v-else-if="stats" class="dashboard-content">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon users">
            <Users :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_users }}</h3>
            <p class="stat-label">Total de Usuários</p>
            <div class="stat-details">
              <span class="detail-item">{{ stats.active_users }} ativos</span>
              <span class="detail-item">{{ stats.pro_users }} PRO</span>
              <span class="detail-item">{{ stats.admin_users }} Admin</span>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon alerts">
            <Bell :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_alerts }}</h3>
            <p class="stat-label">Total de Alertas</p>
            <div class="stat-details">
              <span class="detail-item">{{ stats.active_alerts }} ativos</span>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon portfolio">
            <Briefcase :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_portfolio_items }}</h3>
            <p class="stat-label">Itens de Portfólio</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon watchlist">
            <Eye :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_watchlist_items }}</h3>
            <p class="stat-label">Itens de Watchlist</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon tickers">
            <TrendingUp :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_ticker_prices }}</h3>
            <p class="stat-label">Ticker Prices</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon scans">
            <BarChart3 :size="24" />
          </div>
          <div class="stat-content">
            <h3 class="stat-value">{{ stats.total_scan_results }}</h3>
            <p class="stat-label">Scan Results</p>
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="charts-grid">
        <div class="chart-card">
          <h3 class="chart-title">Usuários por Role</h3>
          <div class="chart-content">
            <div
              v-for="(count, role) in stats.users_by_role"
              :key="role"
              class="chart-item"
            >
              <div class="chart-item-label">{{ role }}</div>
              <div class="chart-item-bar">
                <div
                  class="chart-item-fill"
                  :style="{ width: `${(count / stats.total_users) * 100}%` }"
                ></div>
              </div>
              <div class="chart-item-value">{{ count }}</div>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h3 class="chart-title">Alertas por Tipo</h3>
          <div class="chart-content">
            <div
              v-for="(count, type) in stats.alerts_by_type"
              :key="type"
              class="chart-item"
            >
              <div class="chart-item-label">{{ type }}</div>
              <div class="chart-item-bar">
                <div
                  class="chart-item-fill"
                  :style="{ width: `${(count / stats.total_alerts) * 100}%` }"
                ></div>
              </div>
              <div class="chart-item-value">{{ count }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 32px;
}

.dashboard-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 16px;
  color: #64748b;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.spinner {
  font-size: 16px;
  color: #64748b;
}

.error-state p {
  color: #dc2626;
  margin-bottom: 16px;
}

.retry-button {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.users {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.stat-icon.alerts {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stat-icon.portfolio {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stat-icon.watchlist {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
}

.stat-icon.tickers {
  background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
  color: white;
}

.stat-icon.scans {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 8px 0;
}

.stat-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}

.detail-item {
  font-size: 12px;
  color: #64748b;
  padding: 4px 8px;
  background: #f1f5f9;
  border-radius: 4px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 20px 0;
}

.chart-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-item-label {
  min-width: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
}

.chart-item-bar {
  flex: 1;
  height: 24px;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
}

.chart-item-fill {
  height: 100%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  transition: width 0.3s ease;
}

.chart-item-value {
  min-width: 40px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>

