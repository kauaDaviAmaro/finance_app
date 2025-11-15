<script setup lang="ts">
import { ref, computed } from 'vue'
import { Edit, Trash2, Search, ChevronLeft, ChevronRight, Eye } from 'lucide-vue-next'

interface Column {
  key: string
  label: string
  sortable?: boolean
  formatter?: (value: any) => string
}

interface Props {
  columns: Column[]
  data: any[]
  loading?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  pageSize?: number
  showActions?: boolean
  actions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchable: true,
  searchPlaceholder: 'Buscar...',
  pageSize: 10,
  showActions: true
})

const emit = defineEmits<{
  edit: [item: any]
  delete: [item: any]
  view?: [item: any]
}>()

const searchQuery = ref('')
const currentPage = ref(1)
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')

const filteredData = computed(() => {
  let result = [...props.data]

  // Search
  if (searchQuery.value && props.searchable) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(item => {
      return props.columns.some(col => {
        const value = item[col.key]
        return value?.toString().toLowerCase().includes(query)
      })
    })
  }

  // Sort
  if (sortColumn.value) {
    result.sort((a, b) => {
      const aVal = a[sortColumn.value!]
      const bVal = b[sortColumn.value!]
      
      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1
      
      const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0
      return sortDirection.value === 'asc' ? comparison : -comparison
    })
  }

  return result
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return filteredData.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredData.value.length / props.pageSize)
})

function handleSort(column: Column) {
  if (!column.sortable) return
  
  if (sortColumn.value === column.key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column.key
    sortDirection.value = 'asc'
  }
}

function formatValue(column: Column, value: any): string {
  if (column.formatter) {
    return column.formatter(value)
  }
  
  if (value === null || value === undefined) {
    return '-'
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Sim' : 'Não'
  }
  
  if (value instanceof Date) {
    return new Date(value).toLocaleString('pt-BR')
  }
  
  return value.toString()
}

function handleEdit(item: any) {
  emit('edit', item)
}

function handleDelete(item: any) {
  if (confirm('Tem certeza que deseja deletar este item?')) {
    emit('delete', item)
  }
}

function handleView(item: any) {
  emit('view', item)
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}
</script>

<template>
  <div class="admin-table-container">
    <!-- Search -->
    <div v-if="searchable" class="table-search">
      <div class="search-input-wrapper">
        <Search :size="18" class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="searchPlaceholder"
          class="search-input"
        />
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrapper">
      <table class="admin-table">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="{ sortable: column.sortable }"
              @click="handleSort(column)"
            >
              <div class="th-content">
                <span>{{ column.label }}</span>
                <span
                  v-if="sortColumn === column.key"
                  class="sort-indicator"
                >
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th v-if="showActions" class="actions-header">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + (showActions ? 1 : 0)" class="loading-cell">
              <div class="loading-spinner">Carregando...</div>
            </td>
          </tr>
          <tr v-else-if="paginatedData.length === 0">
            <td :colspan="columns.length + (showActions ? 1 : 0)" class="empty-cell">
              Nenhum item encontrado
            </td>
          </tr>
          <tr v-else v-for="(item, index) in paginatedData" :key="index">
            <td v-for="column in columns" :key="column.key">
              {{ formatValue(column, item[column.key]) }}
            </td>
            <td v-if="showActions" class="actions-cell">
              <template v-if="!props.actions || props.actions.includes('view')">
                <button @click="handleView(item)" class="action-button view" title="Ver detalhes">
                  <Eye :size="16" />
                </button>
              </template>
              <template v-if="!props.actions || props.actions.includes('edit')">
                <button @click="handleEdit(item)" class="action-button edit" title="Editar">
                  <Edit :size="16" />
                </button>
              </template>
              <template v-if="!props.actions || props.actions.includes('delete')">
                <button @click="handleDelete(item)" class="action-button delete" title="Deletar">
                  <Trash2 :size="16" />
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="table-pagination">
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-button"
      >
        <ChevronLeft :size="18" />
      </button>
      <span class="pagination-info">
        Página {{ currentPage }} de {{ totalPages }} ({{ filteredData.length }} itens)
      </span>
      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-button"
      >
        <ChevronRight :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.admin-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-search {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.search-input-wrapper {
  position: relative;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.table-wrapper {
  overflow-x: auto;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table thead {
  background: #f8fafc;
}

.admin-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e2e8f0;
}

.admin-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.admin-table th.sortable:hover {
  background: #f1f5f9;
}

.th-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-indicator {
  color: #3b82f6;
  font-weight: bold;
}

.admin-table td {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  color: #0f172a;
}

.admin-table tbody tr:hover {
  background: #f8fafc;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 48px 16px;
  color: #64748b;
}

.loading-spinner {
  display: inline-block;
}

.actions-header {
  width: 120px;
  text-align: center;
}

.actions-cell {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button.edit {
  background: #dbeafe;
  color: #2563eb;
}

.action-button.edit:hover {
  background: #bfdbfe;
}

.action-button.delete {
  background: #fee2e2;
  color: #dc2626;
}

.action-button.delete:hover {
  background: #fecaca;
}

.action-button.view {
  background: #e0f2fe;
  color: #0369a1;
}

.action-button.view:hover {
  background: #bae6fd;
}

.table-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-top: 1px solid #e2e8f0;
}

.pagination-info {
  font-size: 14px;
  color: #64748b;
}

.pagination-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.pagination-button:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #3b82f6;
  color: #3b82f6;
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

