<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { financialPlanningApi, portfolioApi, ApiError } from '../services/api/index'
import type {
  InvestmentGoal,
  FinancialPlan,
  RetirementPlan,
  WealthAnalysisResponse
} from '../services/api/types'
import { Target, TrendingUp, Calendar, DollarSign, Loader2, AlertCircle } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref<string | null>(null)

// Data
const goals = ref<InvestmentGoal[]>([])
const plans = ref<FinancialPlan[]>([])
const retirementPlans = ref<RetirementPlan[]>([])
const wealthAnalysis = ref<WealthAnalysisResponse | null>(null)

// Computed
const activeGoals = computed(() => goals.value.filter(g => g.status === 'ACTIVE'))
const completedGoals = computed(() => goals.value.filter(g => g.status === 'COMPLETED'))
const onTrackRetirement = computed(() => retirementPlans.value.filter(r => r.is_on_track))

async function loadData() {
  loading.value = true
  error.value = null
  
  try {
    const [goalsRes, plansRes, retirementRes, wealthRes] = await Promise.all([
      financialPlanningApi.getGoals().catch(() => ({ goals: [] })),
      financialPlanningApi.getPlans().catch(() => ({ plans: [] })),
      financialPlanningApi.getRetirementPlans().catch(() => ({ plans: [] })),
      financialPlanningApi.getWealthAnalysis().catch(() => null)
    ])
    
    goals.value = goalsRes.goals || []
    plans.value = plansRes.plans || []
    retirementPlans.value = retirementRes.plans || []
    wealthAnalysis.value = wealthRes
  } catch (err) {
    if (err instanceof ApiError) {
      error.value = err.message
    } else {
      error.value = 'Erro ao carregar dados. Tente novamente.'
    }
    console.error(err)
  } finally {
    loading.value = false
  }
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

function formatPercentage(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  await loadData()
})
</script>

<template>
  <div class="financial-planning-container">
    <Navbar />
    
    <main class="financial-planning-main">
      <div class="header-section">
        <div class="header-content">
          <div class="title-group">
            <Target :size="32" class="title-icon" />
            <div>
              <h1>Planejamento Financeiro</h1>
              <p class="subtitle">Gerencie metas, projeções e planejamento de aposentadoria</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error-banner">
        <AlertCircle :size="20" />
        <span>{{ error }}</span>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <Loader2 :size="48" class="spinner" />
        <p>Carregando planejamento financeiro...</p>
      </div>

      <!-- Dashboard Content -->
      <div v-else class="dashboard-content">
        <!-- Summary Cards -->
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-header">
              <Target :size="24" class="summary-icon" />
              <h3>Metas Ativas</h3>
            </div>
            <p class="summary-value">{{ activeGoals.length }}</p>
            <p class="summary-label">{{ completedGoals.length }} completadas</p>
          </div>

          <div class="summary-card">
            <div class="summary-header">
              <Calendar :size="24" class="summary-icon" />
              <h3>Planos de Aposentadoria</h3>
            </div>
            <p class="summary-value">{{ retirementPlans.length }}</p>
            <p class="summary-label">{{ onTrackRetirement.length }} no caminho</p>
          </div>

          <div class="summary-card">
            <div class="summary-header">
              <DollarSign :size="24" class="summary-icon" />
              <h3>Patrimônio Atual</h3>
            </div>
            <p class="summary-value">
              {{ wealthAnalysis ? formatCurrency(wealthAnalysis.current_value) : 'N/A' }}
            </p>
            <p v-if="wealthAnalysis?.growth_rate" class="summary-label">
              Crescimento: {{ formatPercentage(wealthAnalysis.growth_rate) }}
            </p>
          </div>

          <div class="summary-card">
            <div class="summary-header">
              <TrendingUp :size="24" class="summary-icon" />
              <h3>Planos Financeiros</h3>
            </div>
            <p class="summary-value">{{ plans.length }}</p>
            <p class="summary-label">Configurados</p>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
          <h2 class="section-title">Ações Rápidas</h2>
          <div class="actions-grid">
            <router-link to="/financial-planning/goals" class="action-card">
              <Target :size="32" />
              <h3>Metas de Investimento</h3>
              <p>Gerencie suas metas financeiras</p>
            </router-link>
            
            <router-link to="/financial-planning/retirement" class="action-card">
              <Calendar :size="32" />
              <h3>Planejamento de Aposentadoria</h3>
              <p>Calcule sua aposentadoria</p>
            </router-link>
            
            <router-link to="/financial-planning/projections" class="action-card">
              <TrendingUp :size="32" />
              <h3>Projeções de Portfólio</h3>
              <p>Veja projeções futuras</p>
            </router-link>
            
            <router-link to="/financial-planning/wealth" class="action-card">
              <DollarSign :size="32" />
              <h3>Análise de Patrimônio</h3>
              <p>Acompanhe evolução do patrimônio</p>
            </router-link>
          </div>
        </div>

        <!-- Active Goals Preview -->
        <div v-if="activeGoals.length > 0" class="goals-preview">
          <h2 class="section-title">Metas Ativas</h2>
          <div class="goals-list">
            <div v-for="goal in activeGoals.slice(0, 3)" :key="goal.id" class="goal-card">
              <div class="goal-header">
                <h3>{{ goal.name }}</h3>
                <span class="goal-status active">Ativa</span>
              </div>
              <div class="goal-progress">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    :style="{ width: `${Math.min(goal.progress_percentage, 100)}%` }"
                  ></div>
                </div>
                <div class="progress-info">
                  <span>{{ formatCurrency(goal.current_amount) }}</span>
                  <span>{{ formatCurrency(goal.target_amount) }}</span>
                </div>
              </div>
              <p class="goal-date">Meta: {{ new Date(goal.target_date).toLocaleDateString('pt-BR') }}</p>
            </div>
          </div>
        </div>

        <!-- Retirement Plans Preview -->
        <div v-if="retirementPlans.length > 0" class="retirement-preview">
          <h2 class="section-title">Planos de Aposentadoria</h2>
          <div class="retirement-list">
            <div v-for="plan in retirementPlans.slice(0, 2)" :key="plan.id" class="retirement-card">
              <div class="retirement-header">
                <h3>Aposentadoria aos {{ plan.retirement_age }} anos</h3>
                <span :class="['status-badge', plan.is_on_track ? 'on-track' : 'off-track']">
                  {{ plan.is_on_track ? 'No caminho' : 'Atenção' }}
                </span>
              </div>
              <div class="retirement-info">
                <div class="info-item">
                  <span class="label">Anos restantes:</span>
                  <span class="value">{{ plan.years_until_retirement }}</span>
                </div>
                <div class="info-item">
                  <span class="label">Projeção:</span>
                  <span class="value">{{ formatCurrency(plan.projected_savings) }}</span>
                </div>
                <div class="info-item">
                  <span class="label">Necessário:</span>
                  <span class="value">{{ formatCurrency(plan.required_savings) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '../styles/financial-planning.css';
</style>

