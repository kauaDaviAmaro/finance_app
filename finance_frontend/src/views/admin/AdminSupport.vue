<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getSupportMessage,
  getSupportMessages,
  updateSupportMessage,
  deleteSupportMessage,
  type SupportMessageAdmin,
  type SupportMessageAdminUpdate
} from '../../services/api/admin.api'

const route = useRoute()
const messages = ref<SupportMessageAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingMessage = ref<SupportMessageAdmin | null>(null)
const formLoading = ref(false)
const selectedStatus = ref<string>((route.query.status as string) || '')

const columns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'category', label: 'Categoria', sortable: true },
  { key: 'subject', label: 'Assunto', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'created_at', label: 'Criado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') },
  { key: 'responded_at', label: 'Respondido em', sortable: true, formatter: (v: string | null) => v ? new Date(v).toLocaleString('pt-BR') : '-' }
]

const formFields = ref<Array<{
  key: string
  label: string
  type: 'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea'
  required?: boolean
  options?: { value: string | number; label: string }[]
  placeholder?: string
}>>([
  { key: 'status', label: 'Status', type: 'select' as const, required: true, options: [
    { value: 'pending', label: 'Pendente' },
    { value: 'in_progress', label: 'Em Progresso' },
    { value: 'resolved', label: 'Resolvido' },
    { value: 'closed', label: 'Fechado' }
  ]},
  { key: 'admin_response', label: 'Resposta do Admin', type: 'textarea' as const, placeholder: 'Digite sua resposta aqui...' }
])

async function loadMessages() {
  try {
    loading.value = true
    const status = selectedStatus.value || undefined
    messages.value = await getSupportMessages(0, 1000, status)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar mensagens de suporte')
  } finally {
    loading.value = false
  }
}

function handleEdit(message: SupportMessageAdmin) {
  editingMessage.value = message
  showForm.value = true
}

function handleDelete(messageItem: SupportMessageAdmin) {
  if (!confirm(`Tem certeza que deseja deletar a mensagem #${messageItem.id}?`)) {
    return
  }
  deleteSupportMessage(messageItem.id)
    .then(() => {
      loadMessages()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar mensagem')
    })
}

function handleView(message: SupportMessageAdmin) {
  editingMessage.value = message
  showForm.value = true
}

async function handleSubmit(formData: any) {
  if (!editingMessage.value) return

  try {
    formLoading.value = true
    const updateData: SupportMessageAdminUpdate = {
      status: formData.status,
      admin_response: formData.admin_response || null
    }
    await updateSupportMessage(editingMessage.value.id, updateData)
    showForm.value = false
    editingMessage.value = null
    loadMessages()
  } catch (error: any) {
    window.alert(error.message || 'Erro ao atualizar mensagem')
  } finally {
    formLoading.value = false
  }
}

function handleCancel() {
  showForm.value = false
  editingMessage.value = null
}

function getStatusBadgeClass(status: string) {
  const classes: Record<string, string> = {
    pending: 'status-badge pending',
    in_progress: 'status-badge in-progress',
    resolved: 'status-badge resolved',
    closed: 'status-badge closed'
  }
  return classes[status] || 'status-badge'
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: 'Pendente',
    in_progress: 'Em Progresso',
    resolved: 'Resolvido',
    closed: 'Fechado'
  }
  return labels[status] || status
}

onMounted(() => {
  loadMessages()
})
</script>

<template>
  <div class="admin-support">
    <div class="header">
      <h1>Mensagens de Suporte</h1>
      <div class="header-actions">
        <select v-model="selectedStatus" @change="loadMessages" class="status-filter">
          <option value="">Todos os Status</option>
          <option value="pending">Pendente</option>
          <option value="in_progress">Em Progresso</option>
          <option value="resolved">Resolvido</option>
          <option value="closed">Fechado</option>
        </select>
        <button @click="loadMessages" class="refresh-button">Atualizar</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>
    <div v-else>
      <AdminTable
        :columns="columns"
        :data="messages"
        :actions="['view', 'edit', 'delete']"
        @view="handleView"
        @edit="handleEdit"
        @delete="handleDelete"
      >
        <template #cell-status="{ row }">
          <span :class="getStatusBadgeClass(row.status)">
            {{ getStatusLabel(row.status) }}
          </span>
        </template>
        <template #cell-subject="{ row }">
          <div class="subject-cell">
            <strong>{{ row.subject }}</strong>
            <span class="category-badge">{{ row.category }}</span>
          </div>
        </template>
      </AdminTable>
    </div>

    <AdminForm
      v-if="showForm && editingMessage"
      :fields="formFields"
      :initial-data="{
        status: editingMessage.status,
        admin_response: editingMessage.admin_response || ''
      }"
      :loading="formLoading"
      :title="`Mensagem #${editingMessage.id}`"
      submit-label="Atualizar"
      @submit="handleSubmit"
      @cancel="handleCancel"
    >
      <template #form-content>
        <div class="message-details">
          <div class="detail-section">
            <h3>Detalhes da Mensagem</h3>
            <div class="detail-item">
              <strong>Email:</strong> {{ editingMessage.email }}
            </div>
            <div class="detail-item">
              <strong>Categoria:</strong> {{ editingMessage.category }}
            </div>
            <div class="detail-item">
              <strong>Assunto:</strong> {{ editingMessage.subject }}
            </div>
            <div class="detail-item">
              <strong>Mensagem:</strong>
              <div class="message-text">{{ editingMessage.message }}</div>
            </div>
            <div class="detail-item">
              <strong>Criado em:</strong> {{ new Date(editingMessage.created_at).toLocaleString('pt-BR') }}
            </div>
            <div v-if="editingMessage.responded_at" class="detail-item">
              <strong>Respondido em:</strong> {{ new Date(editingMessage.responded_at).toLocaleString('pt-BR') }}
            </div>
          </div>
        </div>
      </template>
    </AdminForm>
  </div>
</template>

<style scoped>
.admin-support {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.status-filter {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.refresh-button {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-button:hover {
  background: #2563eb;
}

.loading {
  text-align: center;
  padding: 48px;
  color: #64748b;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.in-progress {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.resolved {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.closed {
  background: #e5e7eb;
  color: #374151;
}

.subject-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 4px;
  font-size: 11px;
  width: fit-content;
}

.message-details {
  margin-bottom: 24px;
}

.detail-section {
  background: #f8fafc;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.detail-item {
  margin-bottom: 12px;
  font-size: 14px;
  color: #475569;
}

.detail-item strong {
  color: #0f172a;
  margin-right: 8px;
}

.message-text {
  margin-top: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>

