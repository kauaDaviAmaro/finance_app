<template>
  <div class="backtesting-page">
    <Navbar />
    <div class="backtesting-main">
      <div class="backtesting-header">
        <div class="backtesting-header-card">
          <div class="backtesting-header-content">
            <h1>Backtesting de Estratégias</h1>
            <p class="backtesting-subtitle">Crie e teste estratégias de trading com dados históricos</p>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <AlertCircle class="icon" />
        <span>{{ error }}</span>
        <button @click="error = null" class="close-btn">
          <X />
        </button>
      </div>

      <div class="backtesting-tabs">
        <button 
          :class="['backtesting-tab', { active: activeTab === 'strategies' }]"
          @click="activeTab = 'strategies'"
        >
          <Settings class="icon" />
          Estratégias
        </button>
        <button 
          :class="['backtesting-tab', { active: activeTab === 'backtest' }]"
          @click="activeTab = 'backtest'"
        >
          <BarChart class="icon" />
          Executar Backtest
        </button>
        <button 
          v-if="isPro"
          :class="['backtesting-tab', { active: activeTab === 'compare' }]"
          @click="activeTab = 'compare'"
        >
          <TrendingUp class="icon" />
          Comparar Estratégias
        </button>
        <button 
          v-if="isPro"
          :class="['backtesting-tab', { active: activeTab === 'json' }]"
          @click="activeTab = 'json'"
        >
          <Code class="icon" />
          Editor JSON (PRO)
        </button>
      </div>

      <!-- Tab: Estratégias -->
      <div v-if="activeTab === 'strategies'" class="backtesting-tab-content">
        <div class="section-header">
          <h2>Minhas Estratégias</h2>
          <button @click="showCreateForm = true" class="btn-primary">
            <Plus />
            Nova Estratégia
          </button>
        </div>

        <div v-if="loading" class="loading">
          <Loader2 class="spinner" />
          <span>Carregando estratégias...</span>
        </div>

        <div v-else-if="strategies.length === 0" class="empty-state">
          <Settings class="icon" />
          <p>Nenhuma estratégia criada ainda</p>
          <button @click="showCreateForm = true" class="btn-primary">
            Criar Primeira Estratégia
          </button>
        </div>

        <div v-else class="strategies-grid">
          <div v-for="strategy in strategies" :key="strategy.id" class="strategy-card">
            <div class="strategy-header">
              <h3>{{ strategy.name }}</h3>
              <div class="strategy-actions">
                <button @click="editStrategy(strategy)" class="icon-btn">
                  <Edit2 />
                </button>
                <button @click="deleteStrategy(strategy.id)" class="icon-btn danger">
                  <Trash2 />
                </button>
              </div>
            </div>
            <p v-if="strategy.description" class="strategy-description">{{ strategy.description }}</p>
            <div class="strategy-info">
              <span class="strategy-badge">{{ strategy.strategy_type }}</span>
              <span>Capital: R$ {{ formatCurrency(strategy.initial_capital) }}</span>
              <span>Posição: {{ strategy.position_size }}%</span>
            </div>
            <div class="conditions-preview">
              <strong>Condições:</strong>
              <div v-for="(cond, idx) in strategy.conditions" :key="idx" class="condition-item">
                <span class="condition-type">{{ cond.condition_type }}:</span>
                <span>{{ cond.indicator }} {{ cond.operator }} {{ cond.value || 'N/A' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Executar Backtest -->
      <div v-if="activeTab === 'backtest'" class="backtesting-tab-content">
        <div class="backtest-form">
          <h2>Executar Backtest</h2>
          <div class="form-group">
            <label>Estratégia</label>
            <select v-model="backtestForm.strategy_id" required>
              <option value="">Selecione uma estratégia</option>
              <option v-for="s in strategies" :key="s.id" :value="s.id">
                {{ s.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Ticker</label>
            <input v-model="backtestForm.ticker" type="text" placeholder="Ex: PETR4" required />
          </div>
          <div class="form-group">
            <label>Período</label>
            <select v-model="backtestForm.period">
              <option value="1y">1 Ano</option>
              <option value="6mo">6 Meses</option>
              <option value="3mo">3 Meses</option>
              <option value="1mo">1 Mês</option>
            </select>
          </div>
          <button 
            @click="runBacktest" 
            :disabled="runningBacktest || !backtestForm.strategy_id"
            class="btn-primary"
          >
            <Loader2 v-if="runningBacktest" class="spinner" />
            <BarChart v-else />
            {{ runningBacktest ? 'Executando...' : 'Executar Backtest' }}
          </button>
        </div>

        <div v-if="backtestResult" class="backtest-results">
          <h2>Resultados</h2>
          <div class="metrics-grid">
            <div class="metric-card">
              <span class="metric-label">Retorno Total</span>
              <span :class="['metric-value', backtestResult.total_return && backtestResult.total_return > 0 ? 'positive' : 'negative']">
                {{ formatPercent(backtestResult.total_return) }}
              </span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Retorno Anualizado</span>
              <span :class="['metric-value', backtestResult.annualized_return && backtestResult.annualized_return > 0 ? 'positive' : 'negative']">
                {{ formatPercent(backtestResult.annualized_return) }}
              </span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Sharpe Ratio</span>
              <span class="metric-value">{{ formatNumber(backtestResult.sharpe_ratio) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Max Drawdown</span>
              <span class="metric-value negative">{{ formatPercent(backtestResult.max_drawdown) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Win Rate</span>
              <span class="metric-value">{{ formatPercent(backtestResult.win_rate) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Total Trades</span>
              <span class="metric-value">{{ backtestResult.total_trades }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Comparar Estratégias (PRO) -->
      <div v-if="activeTab === 'compare' && isPro" class="backtesting-tab-content">
        <div class="compare-section">
          <h2>Comparar Estratégias</h2>
          <p class="section-description">Compare o desempenho de múltiplas estratégias no mesmo período</p>
          
          <div class="compare-form">
            <div class="form-group">
              <label>Ticker</label>
              <input v-model="compareForm.ticker" type="text" placeholder="Ex: PETR4" required />
            </div>
            <div class="form-group">
              <label>Período</label>
              <select v-model="compareForm.period">
                <option value="1y">1 Ano</option>
                <option value="6mo">6 Meses</option>
                <option value="3mo">3 Meses</option>
                <option value="1mo">1 Mês</option>
              </select>
            </div>
            <div class="form-group">
              <label>Estratégias (selecione pelo menos 2)</label>
              <div v-if="strategies.length === 0" class="no-strategies-message">
                <p>Nenhuma estratégia disponível. Crie estratégias primeiro na aba "Estratégias".</p>
              </div>
              <div v-else class="strategies-checkbox-list">
                <div 
                  v-for="strategy in strategies" 
                  :key="strategy.id" 
                  class="checkbox-item"
                  @click="toggleStrategy(strategy.id)"
                >
                  <div class="checkbox-wrapper">
                    <input 
                      type="checkbox" 
                      :value="strategy.id" 
                      v-model="compareForm.strategy_ids"
                      @click.stop
                      @change="() => {}"
                    />
                    <div class="checkbox-custom" :class="{ checked: compareForm.strategy_ids.includes(strategy.id) }">
                      <svg v-if="compareForm.strategy_ids.includes(strategy.id)" class="check-icon" viewBox="0 0 20 20" fill="none">
                        <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill="currentColor"/>
                      </svg>
                    </div>
                  </div>
                  <div class="checkbox-content">
                    <span class="strategy-name">{{ strategy.name }}</span>
                    <span class="strategy-type">{{ strategy.strategy_type }}</span>
                  </div>
                </div>
              </div>
              <div v-if="compareForm.strategy_ids.length > 0" class="selected-count">
                {{ compareForm.strategy_ids.length }} estratégia(s) selecionada(s)
              </div>
            </div>
            <button 
              @click="runCompare" 
              :disabled="comparing || compareForm.strategy_ids.length < 2 || !compareForm.ticker || strategies.length === 0"
              class="btn-primary"
            >
              <Loader2 v-if="comparing" class="spinner" />
              <TrendingUp v-else />
              {{ comparing ? 'Comparando...' : 'Comparar Estratégias' }}
            </button>
            
            <div v-if="comparing" class="comparing-status">
              <Loader2 class="spinner" />
              <span>Executando backtests para {{ compareForm.strategy_ids.length }} estratégia(s)...</span>
            </div>
          </div>

          <div v-if="compareResults && compareResults.strategies && compareResults.strategies.length > 0" class="compare-results">
            <h3>Resultados da Comparação</h3>
            <div class="compare-info">
              <span class="compare-ticker">{{ compareResults.ticker }}</span>
              <span class="compare-period">{{ compareResults.period }}</span>
            </div>
            <div class="compare-table-container">
              <table class="compare-table">
                <thead>
                  <tr>
                    <th>Estratégia</th>
                    <th>Retorno Total</th>
                    <th>Retorno Anualizado</th>
                    <th>Sharpe Ratio</th>
                    <th>Max Drawdown</th>
                    <th>Win Rate</th>
                    <th>Total Trades</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="result in compareResults.strategies" :key="result.id || result.strategy_id">
                    <td class="strategy-name-cell">
                      <strong>{{ strategies.find(s => s.id === (result.strategy_id || result.id))?.name || 'N/A' }}</strong>
                    </td>
                    <td :class="['metric-cell', result.total_return && parseFloat(String(result.total_return)) > 0 ? 'positive' : 'negative']">
                      {{ formatPercent(result.total_return) }}
                    </td>
                    <td :class="['metric-cell', result.annualized_return && parseFloat(String(result.annualized_return)) > 0 ? 'positive' : 'negative']">
                      {{ formatPercent(result.annualized_return) }}
                    </td>
                    <td class="metric-cell">{{ formatNumber(result.sharpe_ratio) }}</td>
                    <td class="metric-cell negative">{{ formatPercent(result.max_drawdown) }}</td>
                    <td class="metric-cell">{{ formatPercent(result.win_rate) }}</td>
                    <td class="metric-cell">{{ result.total_trades || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else-if="compareResults && compareResults.strategies && compareResults.strategies.length === 0" class="no-results">
            <p>Nenhum resultado encontrado. Verifique se as estratégias selecionadas são válidas.</p>
          </div>
        </div>
      </div>

      <!-- Tab: Editor JSON (PRO) -->
      <div v-if="activeTab === 'json' && isPro" class="backtesting-tab-content">
        <div class="json-editor-section">
          <h2>Editor JSON de Estratégias</h2>
          <p class="section-description">Crie estratégias avançadas usando configuração JSON customizada</p>
          
          <div class="json-editor-container">
            <div class="json-editor-header">
              <div class="form-group-inline">
                <label>Nome da Estratégia</label>
                <input v-model="jsonStrategyForm.name" type="text" placeholder="Ex: Estratégia Avançada" />
              </div>
              <div class="form-group-inline">
                <label>Descrição</label>
                <input v-model="jsonStrategyForm.description" type="text" placeholder="Descrição opcional" />
              </div>
            </div>
            
            <div class="form-group">
              <label>Configuração JSON</label>
              <textarea 
                v-model="jsonStrategyForm.json_config_text" 
                class="json-textarea"
                placeholder='{"entry_conditions": [...], "exit_conditions": [...]}'
                rows="20"
              ></textarea>
              <small class="help-text">
                Formato JSON esperado: objeto com "entry_conditions" e "exit_conditions" como arrays de condições
              </small>
            </div>

            <div class="json-editor-params">
              <div class="form-group-inline">
                <label>Capital Inicial</label>
                <input v-model.number="jsonStrategyForm.initial_capital" type="number" min="0" step="0.01" />
              </div>
              <div class="form-group-inline">
                <label>Tamanho da Posição (%)</label>
                <input v-model.number="jsonStrategyForm.position_size" type="number" min="0" max="100" step="0.01" />
              </div>
            </div>

            <div class="json-editor-actions">
              <button @click="validateJSON" class="btn-secondary">
                <Code />
                Validar JSON
              </button>
              <button 
                @click="saveJSONStrategy" 
                :disabled="savingJSON || !jsonStrategyForm.name || !jsonStrategyForm.json_config_text"
                class="btn-primary"
              >
                <Loader2 v-if="savingJSON" class="spinner" />
                <Save v-else />
                {{ savingJSON ? 'Salvando...' : 'Salvar Estratégia JSON' }}
              </button>
            </div>

            <div v-if="jsonValidationError" class="json-error">
              <AlertCircle class="icon" />
              <span>Erro de validação: {{ jsonValidationError }}</span>
            </div>

            <div v-if="jsonValidationSuccess" class="json-success">
              <CheckCircle class="icon" />
              <span>JSON válido!</span>
            </div>
          </div>

          <div class="json-example">
            <h3>Exemplo de Configuração JSON</h3>
            <pre class="json-example-code">{{ jsonExample }}</pre>
          </div>
        </div>
      </div>

      <!-- Modal: Criar/Editar Estratégia -->
      <div v-if="showCreateForm || editingStrategy" class="modal-overlay" @click="closeModal">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h2>{{ editingStrategy ? 'Editar' : 'Nova' }} Estratégia</h2>
            <button @click="closeModal" class="close-btn">
              <X />
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Nome</label>
              <input v-model="strategyForm.name" type="text" required />
            </div>
            <div class="form-group">
              <label>Descrição</label>
              <textarea v-model="strategyForm.description" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>Capital Inicial</label>
              <input v-model.number="strategyForm.initial_capital" type="number" min="0" step="0.01" />
            </div>
            <div class="form-group">
              <label>Tamanho da Posição (%)</label>
              <input v-model.number="strategyForm.position_size" type="number" min="0" max="100" step="0.01" />
            </div>
            <div class="conditions-section">
              <h3>Condições de Entrada</h3>
              <div v-for="(cond, idx) in entryConditions" :key="idx" class="condition-row">
                <select v-model="cond.indicator">
                  <option value="RSI">RSI</option>
                  <option value="MACD">MACD</option>
                  <option value="MACD_SIGNAL">MACD Signal</option>
                  <option value="MACD_HISTOGRAM">MACD Histogram</option>
                  <option value="CLOSE">Preço Fechamento</option>
                </select>
                <select v-model="cond.operator">
                  <option value="GREATER_THAN">Maior que</option>
                  <option value="LESS_THAN">Menor que</option>
                  <option value="GREATER_EQUAL">Maior ou igual</option>
                  <option value="LESS_EQUAL">Menor ou igual</option>
                </select>
                <input v-model.number="cond.value" type="number" step="0.01" placeholder="Valor" />
                <button @click="removeCondition('entry', idx)" class="icon-btn danger">
                  <Trash2 />
                </button>
              </div>
              <button @click="addCondition('entry')" class="btn-secondary">
                <Plus />
                Adicionar Condição
              </button>
            </div>
            <div class="conditions-section">
              <h3>Condições de Saída</h3>
              <div v-for="(cond, idx) in exitConditions" :key="idx" class="condition-row">
                <select v-model="cond.indicator">
                  <option value="RSI">RSI</option>
                  <option value="MACD">MACD</option>
                  <option value="MACD_SIGNAL">MACD Signal</option>
                  <option value="MACD_HISTOGRAM">MACD Histogram</option>
                  <option value="CLOSE">Preço Fechamento</option>
                </select>
                <select v-model="cond.operator">
                  <option value="GREATER_THAN">Maior que</option>
                  <option value="LESS_THAN">Menor que</option>
                  <option value="GREATER_EQUAL">Maior ou igual</option>
                  <option value="LESS_EQUAL">Menor ou igual</option>
                </select>
                <input v-model.number="cond.value" type="number" step="0.01" placeholder="Valor" />
                <button @click="removeCondition('exit', idx)" class="icon-btn danger">
                  <Trash2 />
                </button>
              </div>
              <button @click="addCondition('exit')" class="btn-secondary">
                <Plus />
                Adicionar Condição
              </button>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeModal" class="btn-secondary">Cancelar</button>
            <button @click="saveStrategy" :disabled="saving" class="btn-primary">
              <Loader2 v-if="saving" class="spinner" />
              {{ saving ? 'Salvando...' : 'Salvar' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { backtestingApi, ApiError } from '../services/api/index'
import type { 
  Strategy, StrategyCreate, StrategyCreateJSON, BacktestRunRequest, 
  Backtest, BacktestCompareRequest, BacktestCompareResult 
} from '../services/api/types'
import { 
  Settings, BarChart, Plus, Trash2, Loader2, AlertCircle, X, 
  Edit2, TrendingUp, Code, Save, CheckCircle
} from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'

const authStore = useAuthStore()
const isPro = computed(() => authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN')

const activeTab = ref<'strategies' | 'backtest' | 'compare' | 'json'>('strategies')
const strategies = ref<Strategy[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showCreateForm = ref(false)
const editingStrategy = ref<Strategy | null>(null)
const saving = ref(false)
const runningBacktest = ref(false)
const backtestResult = ref<Backtest | null>(null)

// Comparar estratégias
const comparing = ref(false)
const compareForm = ref({
  strategy_ids: [] as number[],
  ticker: '',
  period: '1y',
})
const compareResults = ref<BacktestCompareResult | null>(null)

// Editor JSON
const savingJSON = ref(false)
const jsonValidationError = ref<string | null>(null)
const jsonValidationSuccess = ref(false)
const jsonStrategyForm = ref({
  name: '',
  description: '',
  json_config_text: '',
  initial_capital: 100000,
  position_size: 100,
})
const jsonExample = ref(`{
  "entry_conditions": [
    {
      "indicator": "RSI",
      "operator": "LESS_THAN",
      "value": 30,
      "logic": "AND"
    },
    {
      "indicator": "MACD",
      "operator": "GREATER_THAN",
      "value": 0,
      "logic": "AND"
    }
  ],
  "exit_conditions": [
    {
      "indicator": "RSI",
      "operator": "GREATER_THAN",
      "value": 70,
      "logic": "OR"
    }
  ]
}`)

const strategyForm = ref({
  name: '',
  description: '',
  initial_capital: 100000,
  position_size: 100,
})

const entryConditions = ref<Array<{ indicator: string; operator: string; value?: number; logic: 'AND' | 'OR' }>>([])
const exitConditions = ref<Array<{ indicator: string; operator: string; value?: number; logic: 'AND' | 'OR' }>>([])

const backtestForm = ref<BacktestRunRequest>({
  strategy_id: 0,
  ticker: '',
  period: '1y',
})

function addCondition(type: 'entry' | 'exit') {
  const condition = {
    indicator: 'RSI',
    operator: 'GREATER_THAN',
    value: undefined as number | undefined,
    logic: 'AND' as 'AND' | 'OR',
  }
  if (type === 'entry') {
    entryConditions.value.push(condition)
  } else {
    exitConditions.value.push(condition)
  }
}

function removeCondition(type: 'entry' | 'exit', index: number) {
  if (type === 'entry') {
    entryConditions.value.splice(index, 1)
  } else {
    exitConditions.value.splice(index, 1)
  }
}

async function loadStrategies() {
  loading.value = true
  error.value = null
  try {
    strategies.value = await backtestingApi.getStrategies()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar estratégias'
  } finally {
    loading.value = false
  }
}

function editStrategy(strategy: Strategy) {
  editingStrategy.value = strategy
  strategyForm.value = {
    name: strategy.name,
    description: strategy.description || '',
    initial_capital: strategy.initial_capital,
    position_size: strategy.position_size,
  }
  entryConditions.value = strategy.conditions
    .filter(c => c.condition_type === 'ENTRY')
    .map(c => ({
      indicator: c.indicator,
      operator: c.operator,
      value: c.value || undefined,
      logic: c.logic,
    }))
  exitConditions.value = strategy.conditions
    .filter(c => c.condition_type === 'EXIT')
    .map(c => ({
      indicator: c.indicator,
      operator: c.operator,
      value: c.value || undefined,
      logic: c.logic,
    }))
  showCreateForm.value = true
}

function closeModal() {
  showCreateForm.value = false
  editingStrategy.value = null
  strategyForm.value = {
    name: '',
    description: '',
    initial_capital: 100000,
    position_size: 100,
  }
  entryConditions.value = []
  exitConditions.value = []
}

async function saveStrategy() {
  if (!strategyForm.value.name) {
    error.value = 'Nome da estratégia é obrigatório'
    return
  }

  saving.value = true
  error.value = null
  try {
    const conditions = [
      ...entryConditions.value.map((c, idx) => ({
        condition_type: 'ENTRY' as const,
        indicator: c.indicator,
        operator: c.operator,
        value: c.value,
        logic: c.logic,
        order: idx,
      })),
      ...exitConditions.value.map((c, idx) => ({
        condition_type: 'EXIT' as const,
        indicator: c.indicator,
        operator: c.operator,
        value: c.value,
        logic: c.logic,
        order: idx,
      })),
    ]

    const strategyData: StrategyCreate = {
      name: strategyForm.value.name,
      description: strategyForm.value.description || null,
      initial_capital: strategyForm.value.initial_capital,
      position_size: strategyForm.value.position_size,
      conditions,
    }

    if (editingStrategy.value) {
      await backtestingApi.updateStrategy(editingStrategy.value.id, strategyData)
    } else {
      await backtestingApi.createStrategy(strategyData)
    }

    await loadStrategies()
    closeModal()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao salvar estratégia'
  } finally {
    saving.value = false
  }
}

async function deleteStrategy(id: number) {
  if (!confirm('Tem certeza que deseja deletar esta estratégia?')) return

  try {
    await backtestingApi.deleteStrategy(id)
    await loadStrategies()
  } catch (e: any) {
    error.value = e?.message || 'Erro ao deletar estratégia'
  }
}

async function runBacktest() {
  if (!backtestForm.value.strategy_id || !backtestForm.value.ticker) {
    error.value = 'Preencha todos os campos'
    return
  }

  runningBacktest.value = true
  error.value = null
  try {
    backtestResult.value = await backtestingApi.runBacktest(backtestForm.value)
  } catch (e: any) {
    error.value = e?.message || 'Erro ao executar backtest'
  } finally {
    runningBacktest.value = false
  }
}

function formatCurrency(value: number | null | undefined | string) {
  if (value === null || value === undefined || value === '') return '-'
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '-'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

function formatPercent(value: number | null | undefined | string) {
  if (value === null || value === undefined || value === '') return '-'
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '-'
  return `${numValue.toFixed(2)}%`
}

function formatNumber(value: number | null | undefined | string) {
  if (value === null || value === undefined || value === '') return '-'
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '-'
  return numValue.toFixed(2)
}

function toggleStrategy(strategyId: number) {
  const index = compareForm.value.strategy_ids.indexOf(strategyId)
  if (index > -1) {
    compareForm.value.strategy_ids.splice(index, 1)
  } else {
    compareForm.value.strategy_ids.push(strategyId)
  }
  // Forçar reatividade
  compareForm.value = { ...compareForm.value }
}

async function runCompare() {
  if (!compareForm.value.ticker || compareForm.value.ticker.trim() === '') {
    error.value = 'Informe o ticker'
    return
  }

  if (compareForm.value.strategy_ids.length < 2) {
    error.value = 'Selecione pelo menos 2 estratégias para comparar'
    return
  }

  comparing.value = true
  error.value = null
  compareResults.value = null
  
  try {
    const requestData: BacktestCompareRequest = {
      strategy_ids: compareForm.value.strategy_ids,
      ticker: compareForm.value.ticker.toUpperCase().trim(),
      period: compareForm.value.period || '1y'
    }
    
    console.log('Enviando requisição de comparação:', requestData)
    
    compareResults.value = await backtestingApi.compareStrategies(requestData)
    
    console.log('Resultado recebido:', compareResults.value)
    
    if (!compareResults.value) {
      error.value = 'Nenhum resultado retornado do servidor.'
      return
    }
    
    if (!compareResults.value.strategies || compareResults.value.strategies.length === 0) {
      error.value = 'Nenhuma estratégia retornou resultados válidos. Verifique se as estratégias possuem condições definidas e se o ticker é válido.'
      compareResults.value = null
    } else {
      // Limpar erro se houver resultados
      error.value = null
    }
  } catch (e: any) {
    console.error('Erro ao comparar estratégias:', e)
    console.error('Detalhes do erro:', e?.response?.data)
    
    let errorMessage = 'Erro ao comparar estratégias. '
    
    if (e?.response?.data?.detail) {
      errorMessage += e.response.data.detail
    } else if (e?.message) {
      errorMessage += e.message
    } else {
      errorMessage += 'Tente novamente.'
    }
    
    error.value = errorMessage
    compareResults.value = null
  } finally {
    comparing.value = false
  }
}

function validateJSON() {
  jsonValidationError.value = null
  jsonValidationSuccess.value = false

  if (!jsonStrategyForm.value.json_config_text.trim()) {
    jsonValidationError.value = 'JSON não pode estar vazio'
    return
  }

  try {
    const parsed = JSON.parse(jsonStrategyForm.value.json_config_text)
    
    if (typeof parsed !== 'object' || parsed === null) {
      jsonValidationError.value = 'JSON deve ser um objeto'
      return
    }

    if (!parsed.entry_conditions && !parsed.exit_conditions) {
      jsonValidationError.value = 'JSON deve conter "entry_conditions" ou "exit_conditions"'
      return
    }

    if (parsed.entry_conditions && !Array.isArray(parsed.entry_conditions)) {
      jsonValidationError.value = '"entry_conditions" deve ser um array'
      return
    }

    if (parsed.exit_conditions && !Array.isArray(parsed.exit_conditions)) {
      jsonValidationError.value = '"exit_conditions" deve ser um array'
      return
    }

    jsonValidationSuccess.value = true
  } catch (e: any) {
    jsonValidationError.value = `JSON inválido: ${e.message}`
  }
}

async function saveJSONStrategy() {
  if (!jsonStrategyForm.value.name || !jsonStrategyForm.value.json_config_text) {
    error.value = 'Preencha nome e configuração JSON'
    return
  }

  // Validar JSON antes de salvar
  validateJSON()
  if (jsonValidationError.value) {
    error.value = jsonValidationError.value
    return
  }

  savingJSON.value = true
  error.value = null
  try {
    let jsonConfig
    try {
      jsonConfig = JSON.parse(jsonStrategyForm.value.json_config_text)
    } catch (e) {
      error.value = 'JSON inválido'
      return
    }

    const strategyData: StrategyCreateJSON = {
      name: jsonStrategyForm.value.name,
      description: jsonStrategyForm.value.description || null,
      json_config: jsonConfig,
      initial_capital: jsonStrategyForm.value.initial_capital,
      position_size: jsonStrategyForm.value.position_size,
    }

    await backtestingApi.createStrategyJSON(strategyData)
    await loadStrategies()
    
    // Reset form
    jsonStrategyForm.value = {
      name: '',
      description: '',
      json_config_text: '',
      initial_capital: 100000,
      position_size: 100,
    }
    jsonValidationSuccess.value = false
    jsonValidationError.value = null
  } catch (e: any) {
    error.value = e?.message || 'Erro ao salvar estratégia JSON'
  } finally {
    savingJSON.value = false
  }
}

onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
@import '../styles/backtesting.css';
</style>

