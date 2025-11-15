<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getPortfolioItem,
  getPortfolioItems,
  createPortfolioItem,
  updatePortfolioItem,
  deletePortfolioItem,
  getPortfolios,
  createPortfolio,
  updatePortfolio,
  deletePortfolio,
  type PortfolioItemAdmin,
  type PortfolioItemAdminCreate,
  type PortfolioItemAdminUpdate,
  type PortfolioAdmin,
  type PortfolioAdminCreate,
  type PortfolioAdminUpdate
} from '../../services/api/admin.api'
import { getUsers, type UserAdmin } from '../../services/api/admin.api'

const items = ref<PortfolioItemAdmin[]>([])
const portfolios = ref<PortfolioAdmin[]>([])
const users = ref<UserAdmin[]>([])
const loading = ref(false)
const loadingPortfolios = ref(false)
const showForm = ref(false)
const showPortfolioForm = ref(false)
const editingItem = ref<PortfolioItemAdmin | null>(null)
const editingPortfolio = ref<PortfolioAdmin | null>(null)
const formLoading = ref(false)
const activeTab = ref<'portfolios' | 'items'>('portfolios')

const portfolioColumns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'user_id', label: 'User ID', sortable: true },
  { key: 'name', label: 'Nome', sortable: true },
  { key: 'category', label: 'Categoria', sortable: true },
  { key: 'item_count', label: 'Itens', sortable: true },
  { key: 'created_at', label: 'Criado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const itemColumns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'user_id', label: 'User ID', sortable: true },
  { key: 'portfolio_id', label: 'Portfolio ID', sortable: true },
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'quantity', label: 'Quantidade', sortable: true },
  { key: 'purchase_price', label: 'Preço Compra', sortable: true },
  { key: 'purchase_date', label: 'Data Compra', sortable: true, formatter: (v: string) => new Date(v).toLocaleDateString('pt-BR') },
  { key: 'sold_price', label: 'Preço Venda', sortable: true },
  { key: 'sold_date', label: 'Data Venda', sortable: true, formatter: (v: string | null) => v ? new Date(v).toLocaleDateString('pt-BR') : '-' },
  { key: 'created_at', label: 'Criado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const portfolioFormFields = computed(() => {
  const baseFields: any[] = [
    { key: 'user_id', label: 'User', type: 'select' as const, required: true, options: users.value.map(u => ({ value: u.id, label: `${u.username} (${u.email})` })) },
    { key: 'name', label: 'Nome', type: 'text' as const, required: true },
    { key: 'category', label: 'Categoria', type: 'text' as const },
    { key: 'description', label: 'Descrição', type: 'textarea' as const }
  ]
  return baseFields
})

const itemFormFields = computed(() => {
  const baseFields: any[] = [
    { key: 'user_id', label: 'User', type: 'select' as const, required: true, options: users.value.map(u => ({ value: u.id, label: `${u.username} (${u.email})` })) },
    { key: 'portfolio_id', label: 'Portfolio', type: 'select' as const, required: true, options: portfolios.value.map(p => ({ value: p.id, label: `${p.name} (User ${p.user_id})` })) },
    { key: 'ticker', label: 'Ticker', type: 'text' as const, required: true },
    { key: 'quantity', label: 'Quantidade', type: 'number' as const, required: true, min: 1 },
    { key: 'purchase_price', label: 'Preço de Compra', type: 'number' as const, required: true, min: 0, step: 0.01 },
    { key: 'purchase_date', label: 'Data de Compra', type: 'date' as const, required: true },
    { key: 'sold_price', label: 'Preço de Venda', type: 'number' as const, min: 0, step: 0.01 },
    { key: 'sold_date', label: 'Data de Venda', type: 'date' as const }
  ]
  return baseFields
})

async function loadItems() {
  try {
    loading.value = true
    items.value = await getPortfolioItems(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar itens de portfólio')
  } finally {
    loading.value = false
  }
}

async function loadPortfolios() {
  try {
    loadingPortfolios.value = true
    portfolios.value = await getPortfolios(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar portfolios')
  } finally {
    loadingPortfolios.value = false
  }
}

async function loadUsers() {
  try {
    users.value = await getUsers(0, 1000)
  } catch (error: any) {
    console.error('Erro ao carregar usuários:', error)
  }
}

function handleEdit(item: PortfolioItemAdmin) {
  editingItem.value = item
  showForm.value = true
}

function handleDelete(item: PortfolioItemAdmin) {
  deletePortfolioItem(item.id)
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
    ? updatePortfolioItem(editingItem.value.id, data as PortfolioItemAdminUpdate)
    : createPortfolioItem(data as PortfolioItemAdminCreate)
  
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

function handlePortfolioEdit(portfolio: PortfolioAdmin) {
  editingPortfolio.value = portfolio
  showPortfolioForm.value = true
}

function handlePortfolioDelete(portfolio: PortfolioAdmin) {
  if (confirm(`Tem certeza que deseja deletar o portfolio "${portfolio.name}"?`)) {
    deletePortfolio(portfolio.id)
      .then(() => {
        loadPortfolios()
      })
      .catch((error: any) => {
        window.alert(error.message || 'Erro ao deletar portfolio')
      })
  }
}

function handleNewPortfolio() {
  editingPortfolio.value = null
  showPortfolioForm.value = true
}

function handlePortfolioFormSubmit(data: any) {
  formLoading.value = true
  
  const submitFn = editingPortfolio.value
    ? updatePortfolio(editingPortfolio.value.id, data as PortfolioAdminUpdate)
    : createPortfolio(data as PortfolioAdminCreate)
  
  submitFn
    .then(() => {
      showPortfolioForm.value = false
      editingPortfolio.value = null
      loadPortfolios()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar portfolio')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handlePortfolioFormCancel() {
  showPortfolioForm.value = false
  editingPortfolio.value = null
}

onMounted(() => {
  loadUsers()
  loadPortfolios()
  loadItems()
})
</script>

<template>
  <div class="admin-portfolio">
    <div class="page-header">
      <h1>Gerenciar Portfólio</h1>
      <div class="header-actions">
        <button 
          v-if="activeTab === 'portfolios'"
          @click="handleNewPortfolio" 
          class="new-button"
        >
          Novo Portfolio
        </button>
        <button 
          v-else
          @click="handleNew" 
          class="new-button"
        >
          Novo Item
        </button>
      </div>
    </div>

    <div class="tabs">
      <button 
        :class="['tab-button', { active: activeTab === 'portfolios' }]"
        @click="activeTab = 'portfolios'"
      >
        Portfolios
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'items' }]"
        @click="activeTab = 'items'"
      >
        Itens de Portfolio
      </button>
    </div>

    <AdminTable
      v-if="activeTab === 'portfolios'"
      :columns="portfolioColumns"
      :data="portfolios"
      :loading="loadingPortfolios"
      :actions="['edit', 'delete']"
      @edit="handlePortfolioEdit"
      @delete="handlePortfolioDelete"
    />

    <AdminTable
      v-else
      :columns="itemColumns"
      :data="items"
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="itemFormFields"
          :initial-data="editingItem || undefined"
          :title="editingItem ? 'Editar Item' : 'Novo Item'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>

    <div v-if="showPortfolioForm" class="form-overlay" @click.self="handlePortfolioFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="portfolioFormFields"
          :initial-data="editingPortfolio || undefined"
          :title="editingPortfolio ? 'Editar Portfolio' : 'Novo Portfolio'"
          :loading="formLoading"
          @submit="handlePortfolioFormSubmit"
          @cancel="handlePortfolioFormCancel"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-portfolio {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #e2e8f0;
}

.tab-button {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #3b82f6;
}

.tab-button.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
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

