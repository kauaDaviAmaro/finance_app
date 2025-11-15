<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AdminTable from '../../components/admin/AdminTable.vue'
import AdminForm from '../../components/admin/AdminForm.vue'
import {
  getUser,
  getUsers,
  getUserDetails,
  createUser,
  updateUser,
  deleteUser,
  type UserAdmin,
  type UserAdminCreate,
  type UserAdminUpdate,
  type UserDetails
} from '../../services/api/admin.api'
import { Users, Briefcase, Bell, Eye, MessageSquare, X, ExternalLink } from 'lucide-vue-next'

const users = ref<UserAdmin[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingUser = ref<UserAdmin | null>(null)
const formLoading = ref(false)
const showDetailsModal = ref(false)
const userDetails = ref<UserDetails | null>(null)
const loadingDetails = ref(false)
const activeTab = ref<'info' | 'portfolio' | 'alerts' | 'watchlist' | 'support'>('info')

const columns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'username', label: 'Username', sortable: true },
  { key: 'role', label: 'Role', sortable: true },
  { key: 'is_active', label: 'Ativo', sortable: true },
  { key: 'is_verified', label: 'Verificado', sortable: true },
  { key: 'subscription_status', label: 'Status', sortable: true },
  { key: 'created_at', label: 'Criado em', sortable: true, formatter: (v: string) => new Date(v).toLocaleString('pt-BR') }
]

const formFields = computed(() => {
  const baseFields: any[] = [
    { key: 'email', label: 'Email', type: 'email' as const, required: true },
    { key: 'username', label: 'Username', type: 'text' as const, required: true },
    { key: 'role', label: 'Role', type: 'select' as const, required: true, options: [
      { value: 'USER', label: 'USER' },
      { value: 'PRO', label: 'PRO' },
      { value: 'ADMIN', label: 'ADMIN' }
    ]},
    { key: 'is_active', label: 'Ativo', type: 'checkbox' as const },
    { key: 'is_verified', label: 'Verificado', type: 'checkbox' as const },
    { key: 'subscription_status', label: 'Status de Assinatura', type: 'text' as const },
    { key: 'stripe_customer_id', label: 'Stripe Customer ID', type: 'text' as const }
  ]
  
  // Adiciona campo de senha apenas na criação ou opcional na edição
  if (!editingUser.value) {
    baseFields.splice(2, 0, { key: 'password', label: 'Senha', type: 'text' as const, required: true })
  } else {
    baseFields.splice(2, 0, { key: 'password', label: 'Senha (deixe vazio para não alterar)', type: 'text' as const, required: false })
  }
  
  return baseFields
})

async function loadUsers() {
  try {
    loading.value = true
    users.value = await getUsers(0, 1000)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar usuários')
  } finally {
    loading.value = false
  }
}

function handleEdit(user: UserAdmin) {
  editingUser.value = user
  showForm.value = true
}

function handleDelete(user: UserAdmin) {
  deleteUser(user.id)
    .then(() => {
      loadUsers()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao deletar usuário')
    })
}

function handleNew() {
  editingUser.value = null
  showForm.value = true
}

function handleFormSubmit(data: any) {
  formLoading.value = true
  
  // Se estiver editando e senha estiver vazia, remove do payload
  if (editingUser.value && !data.password) {
    delete data.password
  }
  
  const submitFn = editingUser.value
    ? updateUser(editingUser.value.id, data as UserAdminUpdate)
    : createUser(data as UserAdminCreate)
  
  submitFn
    .then(() => {
      showForm.value = false
      editingUser.value = null
      loadUsers()
    })
    .catch((error: any) => {
      window.alert(error.message || 'Erro ao salvar usuário')
    })
    .finally(() => {
      formLoading.value = false
    })
}

function handleFormCancel() {
  showForm.value = false
  editingUser.value = null
}

async function handleView(user: UserAdmin) {
  try {
    loadingDetails.value = true
    showDetailsModal.value = true
    activeTab.value = 'info'
    userDetails.value = await getUserDetails(user.id)
  } catch (error: any) {
    window.alert(error.message || 'Erro ao carregar detalhes do usuário')
    showDetailsModal.value = false
  } finally {
    loadingDetails.value = false
  }
}

function closeDetailsModal() {
  showDetailsModal.value = false
  userDetails.value = null
  activeTab.value = 'info'
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('pt-BR')
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="admin-users">
    <div class="page-header">
      <h1>Gerenciar Usuários</h1>
      <button @click="handleNew" class="new-button">Novo Usuário</button>
    </div>

    <AdminTable
      :columns="columns"
      :data="users"
      :loading="loading"
      :actions="['view', 'edit', 'delete']"
      @view="handleView"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <div v-if="showForm" class="form-overlay" @click.self="handleFormCancel">
      <div class="form-container">
        <AdminForm
          :fields="formFields"
          :initial-data="editingUser || undefined"
          :title="editingUser ? 'Editar Usuário' : 'Novo Usuário'"
          :loading="formLoading"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
        />
      </div>
    </div>

    <!-- User Details Modal -->
    <div v-if="showDetailsModal" class="modal-overlay" @click.self="closeDetailsModal">
      <div class="details-modal">
        <div class="modal-header">
          <div class="header-left">
            <div class="user-avatar">
              <Users :size="32" />
            </div>
            <div>
              <h2>{{ userDetails?.user.username || 'Usuário' }}</h2>
              <p class="user-email">{{ userDetails?.user.email }}</p>
            </div>
          </div>
          <button @click="closeDetailsModal" class="close-button">
            <X :size="24" />
          </button>
        </div>

        <div class="modal-tabs">
          <button
            :class="['tab-button', { active: activeTab === 'info' }]"
            @click="activeTab = 'info'"
          >
            <Users :size="18" />
            <span>Informações</span>
          </button>
          <button
            :class="['tab-button', { active: activeTab === 'portfolio' }]"
            @click="activeTab = 'portfolio'"
          >
            <Briefcase :size="18" />
            <span>Portfólio ({{ userDetails?.portfolios.length || 0 }})</span>
          </button>
          <button
            :class="['tab-button', { active: activeTab === 'alerts' }]"
            @click="activeTab = 'alerts'"
          >
            <Bell :size="18" />
            <span>Alertas ({{ userDetails?.alerts.length || 0 }})</span>
          </button>
          <button
            :class="['tab-button', { active: activeTab === 'watchlist' }]"
            @click="activeTab = 'watchlist'"
          >
            <Eye :size="18" />
            <span>Watchlist ({{ userDetails?.watchlist_items.length || 0 }})</span>
          </button>
          <button
            :class="['tab-button', { active: activeTab === 'support' }]"
            @click="activeTab = 'support'"
          >
            <MessageSquare :size="18" />
            <span>Suporte ({{ userDetails?.support_messages.length || 0 }})</span>
          </button>
        </div>

        <div class="modal-content">
          <div v-if="loadingDetails" class="loading-content">
            <div class="spinner">Carregando...</div>
          </div>

          <!-- Info Tab -->
          <div v-else-if="activeTab === 'info' && userDetails" class="tab-content">
            <div class="info-grid">
              <div class="info-card">
                <h3>Informações Básicas</h3>
                <div class="info-item">
                  <span class="info-label">ID:</span>
                  <span class="info-value">{{ userDetails.user.id }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Email:</span>
                  <span class="info-value">{{ userDetails.user.email }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Username:</span>
                  <span class="info-value">{{ userDetails.user.username }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Role:</span>
                  <span :class="['role-badge', userDetails.user.role.toLowerCase()]">
                    {{ userDetails.user.role }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">Status:</span>
                  <span :class="['status-badge', userDetails.user.is_active ? 'active' : 'inactive']">
                    {{ userDetails.user.is_active ? 'Ativo' : 'Inativo' }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">Verificado:</span>
                  <span :class="['status-badge', userDetails.user.is_verified ? 'verified' : 'unverified']">
                    {{ userDetails.user.is_verified ? 'Sim' : 'Não' }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">Assinatura:</span>
                  <span class="info-value">{{ userDetails.user.subscription_status || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Criado em:</span>
                  <span class="info-value">{{ formatDate(userDetails.user.created_at) }}</span>
                </div>
              </div>

              <div class="info-card">
                <h3>Estatísticas</h3>
                <div class="stats-grid">
                  <div class="stat-box">
                    <Briefcase :size="24" />
                    <div>
                      <div class="stat-number">{{ userDetails.portfolios.length }}</div>
                      <div class="stat-label">Portfolios</div>
                    </div>
                  </div>
                  <div class="stat-box">
                    <Briefcase :size="24" />
                    <div>
                      <div class="stat-number">{{ userDetails.portfolio_items.length }}</div>
                      <div class="stat-label">Itens no Portfólio</div>
                    </div>
                  </div>
                  <div class="stat-box">
                    <Bell :size="24" />
                    <div>
                      <div class="stat-number">{{ userDetails.alerts.length }}</div>
                      <div class="stat-label">Alertas</div>
                    </div>
                  </div>
                  <div class="stat-box">
                    <Eye :size="24" />
                    <div>
                      <div class="stat-number">{{ userDetails.watchlist_items.length }}</div>
                      <div class="stat-label">Watchlist</div>
                    </div>
                  </div>
                  <div class="stat-box">
                    <MessageSquare :size="24" />
                    <div>
                      <div class="stat-number">{{ userDetails.support_messages.length }}</div>
                      <div class="stat-label">Mensagens</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Portfolio Tab -->
          <div v-else-if="activeTab === 'portfolio' && userDetails" class="tab-content">
            <div v-if="userDetails.portfolios.length === 0" class="empty-state">
              <Briefcase :size="48" />
              <p>Nenhum portfolio criado</p>
            </div>
            <div v-else class="portfolios-list">
              <div
                v-for="portfolio in userDetails.portfolios"
                :key="portfolio.id"
                class="portfolio-card"
              >
                <div class="portfolio-header">
                  <div>
                    <h4>{{ portfolio.name }}</h4>
                    <p v-if="portfolio.category" class="portfolio-category">{{ portfolio.category }}</p>
                    <p v-if="portfolio.description" class="portfolio-description">{{ portfolio.description }}</p>
                  </div>
                  <span class="portfolio-badge">{{ portfolio.item_count || 0 }} itens</span>
                </div>
                <div v-if="userDetails.portfolio_items.filter(item => item.portfolio_id === portfolio.id).length > 0" class="portfolio-items">
                  <h5>Itens do Portfolio:</h5>
                  <div class="items-grid">
                    <div
                      v-for="item in userDetails.portfolio_items.filter(item => item.portfolio_id === portfolio.id)"
                      :key="item.id"
                      class="item-card"
                    >
                      <div class="item-header">
                        <h4>{{ item.ticker }}</h4>
                        <span class="item-badge">{{ item.quantity }} ações</span>
                      </div>
                      <div class="item-details">
                        <div class="detail-row">
                          <span>Preço de Compra:</span>
                          <strong>{{ formatCurrency(item.purchase_price) }}</strong>
                        </div>
                        <div class="detail-row">
                          <span>Data de Compra:</span>
                          <span>{{ new Date(item.purchase_date).toLocaleDateString('pt-BR') }}</span>
                        </div>
                        <div v-if="item.sold_price" class="detail-row">
                          <span>Preço de Venda:</span>
                          <strong>{{ formatCurrency(item.sold_price) }}</strong>
                        </div>
                        <div v-if="item.sold_date" class="detail-row">
                          <span>Data de Venda:</span>
                          <span>{{ new Date(item.sold_date).toLocaleDateString('pt-BR') }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-portfolio">
                  <p>Nenhum item neste portfolio</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Alerts Tab -->
          <div v-else-if="activeTab === 'alerts' && userDetails" class="tab-content">
            <div v-if="userDetails.alerts.length === 0" class="empty-state">
              <Bell :size="48" />
              <p>Nenhum alerta configurado</p>
            </div>
            <div v-else class="items-list">
              <div
                v-for="alert in userDetails.alerts"
                :key="alert.id"
                class="item-card"
              >
                <div class="item-header">
                  <h4>{{ alert.ticker }}</h4>
                  <span :class="['item-badge', alert.is_active ? 'active' : 'inactive']">
                    {{ alert.is_active ? 'Ativo' : 'Inativo' }}
                  </span>
                </div>
                <div class="item-details">
                  <div class="detail-row">
                    <span>Tipo:</span>
                    <strong>{{ alert.indicator_type }}</strong>
                  </div>
                  <div class="detail-row">
                    <span>Condição:</span>
                    <span>{{ alert.condition }}</span>
                  </div>
                  <div v-if="alert.threshold_value" class="detail-row">
                    <span>Valor Limite:</span>
                    <strong>{{ alert.threshold_value }}</strong>
                  </div>
                  <div v-if="alert.triggered_at" class="detail-row">
                    <span>Disparado em:</span>
                    <span>{{ formatDate(alert.triggered_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Watchlist Tab -->
          <div v-else-if="activeTab === 'watchlist' && userDetails" class="tab-content">
            <div v-if="userDetails.watchlist_items.length === 0" class="empty-state">
              <Eye :size="48" />
              <p>Nenhum item na watchlist</p>
            </div>
            <div v-else class="items-list">
              <div
                v-for="item in userDetails.watchlist_items"
                :key="item.id"
                class="item-card"
              >
                <div class="item-header">
                  <h4>{{ item.ticker }}</h4>
                </div>
                <div class="item-details">
                  <div class="detail-row">
                    <span>Adicionado em:</span>
                    <span>{{ formatDate(item.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Support Tab -->
          <div v-else-if="activeTab === 'support' && userDetails" class="tab-content">
            <div v-if="userDetails.support_messages.length === 0" class="empty-state">
              <MessageSquare :size="48" />
              <p>Nenhuma mensagem de suporte</p>
            </div>
            <div v-else class="items-list">
              <div
                v-for="msg in userDetails.support_messages"
                :key="msg.id"
                class="item-card"
              >
                <div class="item-header">
                  <h4>{{ msg.subject }}</h4>
                  <span :class="['item-badge', `status-${msg.status}`]">
                    {{ msg.status }}
                  </span>
                </div>
                <div class="item-details">
                  <div class="detail-row">
                    <span>Categoria:</span>
                    <strong>{{ msg.category }}</strong>
                  </div>
                  <div class="detail-row">
                    <span>Mensagem:</span>
                    <p class="message-text">{{ msg.message }}</p>
                  </div>
                  <div class="detail-row">
                    <span>Criado em:</span>
                    <span>{{ formatDate(msg.created_at) }}</span>
                  </div>
                  <div v-if="msg.admin_response" class="detail-row">
                    <span>Resposta:</span>
                    <p class="message-text response">{{ msg.admin_response }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleEdit(userDetails!.user)" class="footer-button edit">
            <ExternalLink :size="18" />
            <span>Editar Usuário</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-users {
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

/* Details Modal */
.details-modal {
  background: white;
  border-radius: 16px;
  max-width: 1000px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.modal-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.user-email {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.close-button {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-tabs {
  display: flex;
  gap: 4px;
  padding: 0 24px;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  margin-bottom: -1px;
}

.tab-button:hover {
  color: #3b82f6;
  background: #f8fafc;
}

.tab-button.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px;
}

.spinner {
  font-size: 16px;
  color: #64748b;
}

.tab-content {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.info-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
}

.info-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e2e8f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #0f172a;
  font-weight: 600;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.role-badge.admin {
  background: #fef3c7;
  color: #92400e;
}

.role-badge.pro {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge.user {
  background: #e5e7eb;
  color: #374151;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.verified {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.unverified {
  background: #f3f4f6;
  color: #6b7280;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-box svg {
  color: #3b82f6;
  flex-shrink: 0;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  color: #64748b;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.portfolios-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.portfolio-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
}

.portfolio-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.portfolio-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.portfolio-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.portfolio-category {
  font-size: 13px;
  color: #64748b;
  margin: 4px 0;
  font-style: italic;
}

.portfolio-description {
  font-size: 14px;
  color: #475569;
  margin: 8px 0 0 0;
  line-height: 1.5;
}

.portfolio-badge {
  background: #dbeafe;
  color: #1e40af;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.portfolio-items {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.portfolio-items h5 {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 12px 0;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.empty-portfolio {
  margin-top: 16px;
  padding: 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  background: #f8fafc;
  border-radius: 8px;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.item-card:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.item-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.item-badge {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.item-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.item-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.item-badge.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.item-badge.status-resolved {
  background: #d1fae5;
  color: #065f46;
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  font-size: 13px;
  gap: 16px;
}

.detail-row span:first-child {
  color: #64748b;
  font-weight: 500;
}

.detail-row strong {
  color: #0f172a;
  font-weight: 600;
}

.message-text {
  margin: 0;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
  white-space: pre-wrap;
  max-width: 100%;
  word-break: break-word;
}

.message-text.response {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.footer-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.footer-button:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .details-modal {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }

  .modal-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>

