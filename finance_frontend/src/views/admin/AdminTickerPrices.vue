<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getTickerPrice,
  getTickerPrices,
  createTickerPrice,
  updateTickerPrice,
  deleteTickerPrice,
  type TickerPriceAdmin,
  type TickerPriceAdminCreate,
  type TickerPriceAdminUpdate
} from '../../services/api/admin.api'

const prices = ref<TickerPriceAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingPrice = ref<TickerPriceAdmin | null>(null)
const formLoading = ref(false)

const columns = [
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'last_price', label: 'Último Preço', sortable: true, formatter: (v: number) => `R$ ${v.toFixed(2)}` },
  { key: 'timestamp', label: 'Atualizado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const formFields = [
  { key: 'ticker', label: 'Ticker', type: 'text' as const, required: true },
  { key: 'last_price', label: 'Último Preço', type: 'number' as const, required: true, min: 0, step: 0.0001 }
]

async function loadPrices() {
  try {
    loading.value = true
    prices.value = await getTickerPrices(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar preços')
  } finally {
    loading.value = false
  }
}

function handleEdit(price: TickerPriceAdmin) {
  editingPrice.value = price
  showForm.value = true
}

function handleDelete(price: TickerPriceAdmin) {
  deleteTickerPrice(price.ticker)
    .then(() => {
      loadPrices()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar preço')
    })
}

function handleNew() {
  editingPrice.value = null
  showForm.value = true
}

function handleFormSubmit(data: any) {
  formLoading.value = true
  
  const submitFn = editingPrice.value
    ? updateTickerPrice(editingPrice.value.ticker, data as TickerPriceAdminUpdate)
    : createTickerPrice(data as TickerPriceAdminCreate)
  
  submitFn
    .then(() => {
      showForm.value = false
      editingPrice.value = null
      loadPrices()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar preço')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handleFormCancel() {
  showForm.value = false
  editingPrice.value = null
}

onMounted(() => {
  loadPrices()
})
</script>

<template>
  <div class="admin-ticker-prices">
    <div class="page-header">
      <h1>Gerenciar Ticker Prices</h1>
      <button @click="handleNew" class="new-button">Novo Preço</button>
    </div>

    <AdminTable
      :columns="columns"
      :data="prices"
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="formFields"
          :initial-data="editingPrice || undefined"
          :title="editingPrice ? 'Editar Preço' : 'Novo Preço'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-ticker-prices {
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

