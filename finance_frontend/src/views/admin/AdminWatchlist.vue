<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getWatchlistItem,
  getWatchlistItems,
  createWatchlistItem,
  updateWatchlistItem,
  deleteWatchlistItem,
  type WatchlistItemAdmin,
  type WatchlistItemAdminCreate,
  type WatchlistItemAdminUpdate
} from '../../services/api/admin.api'
import { getUsers, type UserAdmin } from '../../services/api/admin.api'

const items = ref<WatchlistItemAdmin[]>([])
const users = ref<UserAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingItem = ref<WatchlistItemAdmin | null>(null)
const formLoading = ref(false)

const columns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'user_id', label: 'User ID', sortable: true },
  { key: 'ticker', label: 'Ticker', sortable: true },
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
  { key: 'ticker', label: 'Ticker', type: 'text' as const, required: true }
])

async function loadItems() {
  try {
    loading.value = true
    items.value = await getWatchlistItems(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar itens de watchlist')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    users.value = await getUsers(0, 1000)
    const userField = formFields.value.find(f => f.key === 'user_id')
    if (userField) {
      userField.type = 'select' as const
      userField.options = users.value.map(u => ({ value: u.id as number, label: `${u.username} (${u.email})` }))
    }
  } catch (error: any) {
    console.error('Erro ao carregar usuários:', error)
  }
}

function handleEdit(item: WatchlistItemAdmin) {
  editingItem.value = item
  showForm.value = true
}

function handleDelete(item: WatchlistItemAdmin) {
  deleteWatchlistItem(item.id)
    .then(() => {
      loadItems()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar item')
    })
}

function handleNew() {
  editingItem.value = null
  showForm.value = true
}

function handleFormSubmit(data: any) {
  formLoading.value = true
  
  const submitFn = editingItem.value
    ? updateWatchlistItem(editingItem.value.id, data as WatchlistItemAdminUpdate)
    : createWatchlistItem(data as WatchlistItemAdminCreate)
  
  submitFn
    .then(() => {
      showForm.value = false
      editingItem.value = null
      loadItems()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar item')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handleFormCancel() {
  showForm.value = false
  editingItem.value = null
}

onMounted(() => {
  loadUsers()
  loadItems()
})
</script>

<template>
  <div class="admin-watchlist">
    <div class="page-header">
      <h1>Gerenciar Watchlist</h1>
      <button @click="handleNew" class="new-button">Novo Item</button>
    </div>

    <AdminTable
      :columns="columns"
      :data="items"
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="formFields"
          :initial-data="editingItem || undefined"
          :title="editingItem ? 'Editar Item' : 'Novo Item'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-watchlist {
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

