<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getAlert,
  getAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  type AlertAdmin,
  type AlertAdminCreate,
  type AlertAdminUpdate
} from '../../services/api/admin.api'
import { getUsers, type UserAdmin } from '../../services/api/admin.api'

const alerts = ref<AlertAdmin[]>([])
const users = ref<UserAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingAlert = ref<AlertAdmin | null>(null)
const formLoading = ref(false)

const columns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'user_id', label: 'User ID', sortable: true },
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'indicator_type', label: 'Indicador', sortable: true },
  { key: 'condition', label: 'Condição', sortable: true },
  { key: 'threshold_value', label: 'Valor Limite', sortable: true },
  { key: 'is_active', label: 'Ativo', sortable: true },
  { key: 'triggered_at', label: 'Disparado em', sortable: true, formatter: (v: string | null) => v ? new Date(v).toLocaleString('pt-BR') : '-' },
  { key: 'created_at', label: 'Criado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const formFields = ref<Array<{
  key: string
  label: string
  type: 'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea'
  required?: boolean
  options?: { value: string | number; label: string }[]
  placeholder?: string
  min?: number
  max?: number
  step?: number
}>>([
  { key: 'user_id', label: 'User ID', type: 'number' as const, required: true },
  { key: 'ticker', label: 'Ticker', type: 'text' as const, required: true },
  { key: 'indicator_type', label: 'Tipo de Indicador', type: 'select' as const, required: true, options: [
    { value: 'MACD', label: 'MACD' },
    { value: 'RSI', label: 'RSI' },
    { value: 'STOCHASTIC', label: 'STOCHASTIC' },
    { value: 'BBANDS', label: 'BBANDS' }
  ]},
  { key: 'condition', label: 'Condição', type: 'select' as const, required: true, options: [
    { value: 'CROSS_ABOVE', label: 'CROSS_ABOVE' },
    { value: 'CROSS_BELOW', label: 'CROSS_BELOW' },
    { value: 'GREATER_THAN', label: 'GREATER_THAN' },
    { value: 'LESS_THAN', label: 'LESS_THAN' }
  ]},
  { key: 'threshold_value', label: 'Valor Limite', type: 'number' as const, step: 0.0001 },
  { key: 'is_active', label: 'Ativo', type: 'checkbox' as const }
])

async function loadAlerts() {
  try {
    loading.value = true
    alerts.value = await getAlerts(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar alertas')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    users.value = await getUsers(0, 1000)
    // Update form field options
    const userField = formFields.value.find(f => f.key === 'user_id')
    if (userField) {
      userField.type = 'select' as const
      userField.options = users.value.map(u => ({ value: u.id as number, label: `${u.username} (${u.email})` }))
    }
  } catch (error: any) {
    console.error('Erro ao carregar usuários:', error)
  }
}

function handleEdit(alert: AlertAdmin) {
  editingAlert.value = alert
  showForm.value = true
}

function handleDelete(alertItem: AlertAdmin) {
  deleteAlert(alertItem.id)
    .then(() => {
      loadAlerts()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar alerta')
    })
}

function handleNew() {
  editingAlert.value = null
  showForm.value = true
}

function handleFormSubmit(data: any) {
  formLoading.value = true
  
  const submitFn = editingAlert.value
    ? updateAlert(editingAlert.value.id, data as AlertAdminUpdate)
    : createAlert(data as AlertAdminCreate)
  
  submitFn
    .then(() => {
      showForm.value = false
      editingAlert.value = null
      loadAlerts()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar alerta')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handleFormCancel() {
  showForm.value = false
  editingAlert.value = null
}

onMounted(() => {
  loadUsers()
  loadAlerts()
})
</script>

<template>
  <div class="admin-alerts">
    <div class="page-header">
      <h1>Gerenciar Alertas</h1>
      <button @click="handleNew" class="new-button">Novo Alerta</button>
    </div>

    <AdminTable
      :columns="columns"
      :data="alerts"
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="formFields"
          :initial-data="editingAlert || undefined"
          :title="editingAlert ? 'Editar Alerta' : 'Novo Alerta'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-alerts {
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

