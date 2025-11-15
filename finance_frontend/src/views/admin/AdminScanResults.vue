<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getScanResult,
  getScanResults,
  createScanResult,
  updateScanResult,
  deleteScanResult,
  type DailyScanResultAdmin,
  type DailyScanResultAdminCreate,
  type DailyScanResultAdminUpdate
} from '../../services/api/admin.api'

const results = ref<DailyScanResultAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingResult = ref<DailyScanResultAdmin | null>(null)
const formLoading = ref(false)

const columns = [
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'last_price', label: 'Último Preço', sortable: true, formatter: (v: number) => `R$ ${v.toFixed(2)}` },
  { key: 'rsi_14', label: 'RSI 14', sortable: true, formatter: (v: number | null) => v ? v.toFixed(2) : '-' },
  { key: 'macd_h', label: 'MACD H', sortable: true, formatter: (v: number | null) => v ? v.toFixed(4) : '-' },
  { key: 'bb_upper', label: 'BB Upper', sortable: true, formatter: (v: number | null) => v ? v.toFixed(2) : '-' },
  { key: 'bb_lower', label: 'BB Lower', sortable: true, formatter: (v: number | null) => v ? v.toFixed(2) : '-' },
  { key: 'timestamp', label: 'Atualizado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const formFields = [
  { key: 'ticker', label: 'Ticker', type: 'text' as const, required: true },
  { key: 'last_price', label: 'Último Preço', type: 'number' as const, required: true, min: 0, step: 0.000001 },
  { key: 'rsi_14', label: 'RSI 14', type: 'number' as const, step: 0.0001 },
  { key: 'macd_h', label: 'MACD H', type: 'number' as const, step: 0.0001 },
  { key: 'bb_upper', label: 'BB Upper', type: 'number' as const, step: 0.000001 },
  { key: 'bb_lower', label: 'BB Lower', type: 'number' as const, step: 0.000001 }
]

async function loadResults() {
  try {
    loading.value = true
    results.value = await getScanResults(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar resultados')
  } finally {
    loading.value = false
  }
}

function handleEdit(result: DailyScanResultAdmin) {
  editingResult.value = result
  showForm.value = true
}

function handleDelete(result: DailyScanResultAdmin) {
  deleteScanResult(result.ticker)
    .then(() => {
      loadResults()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar resultado')
    })
}

function handleNew() {
  editingResult.value = null
  showForm.value = true
}

function handleFormSubmit(data: any) {
  formLoading.value = true
  
  const submitFn = editingResult.value
    ? updateScanResult(editingResult.value.ticker, data as DailyScanResultAdminUpdate)
    : createScanResult(data as DailyScanResultAdminCreate)
  
  submitFn
    .then(() => {
      showForm.value = false
      editingResult.value = null
      loadResults()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar resultado')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handleFormCancel() {
  showForm.value = false
  editingResult.value = null
}

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="admin-scan-results">
    <div class="page-header">
      <h1>Gerenciar Scan Results</h1>
      <button @click="handleNew" class="new-button">Novo Resultado</button>
    </div>

    <AdminTable
      :columns="columns"
      :data="results"
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="formFields"
          :initial-data="editingResult || undefined"
          :title="editingResult ? 'Editar Resultado' : 'Novo Resultado'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-scan-results {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.new-button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.new-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
}

.form-container {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
</style>

