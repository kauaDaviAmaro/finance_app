<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'
import type { Notification } from '../services/api/notifications.api'
import { Coins, BarChart, Eye, Bell, TrendingUp, LogOut, User, Menu, X, DollarSign, Crown, HelpCircle, ChevronDown, CheckCircle, Trash2, AlertCircle, MessageSquare, CreditCard, Settings } from 'lucide-vue-next'
import { changeMyRole } from '../services/api/admin.api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const showMobileMenu = ref(false)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const showRoleMenu = ref(false)
const openGroup = ref<string | null>(null)
const changingRole = ref(false)
let notificationsInterval: ReturnType<typeof setInterval> | null = null

const isGroupActive = (groupName: string) => {
  const groups: Record<string, string[]> = {
    investimentos: ['/home', '/portfolio', '/watchlist'],
    analise: ['/market-analysis', '/scanner'],
    alertas: ['/alerts'],
    ajuda: ['/support']
  }
  return groups[groupName]?.some(path => route.path.startsWith(path)) || false
}

const isPro = computed(() => {
  return authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN'
})

const canChangeRole = computed(() => {
  // Sempre permitir se for admin
  return authStore.isAuthenticated && authStore.user?.role === 'ADMIN'
})

const wasAdmin = computed(() => {
  // Verificar se já foi admin (armazenado no localStorage ou se é admin agora)
  if (authStore.user?.role === 'ADMIN') {
    localStorage.setItem('was_admin', 'true')
    return true
  }
  return localStorage.getItem('was_admin') === 'true'
})

const showRoleButton = computed(() => {
  // Mostrar botão se for admin ou se já foi admin antes
  return authStore.isAuthenticated && (authStore.user?.role === 'ADMIN' || wasAdmin.value)
})

function handleLogout() {
  // Limpar flag de admin ao fazer logout
  localStorage.removeItem('was_admin')
  authStore.logout()
  router.push('/login')
}

function toggleMobileMenu() {
  showMobileMenu.value = !showMobileMenu.value
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

function toggleGroup(groupName: string) {
  if (openGroup.value === groupName) {
    openGroup.value = null
  } else {
    openGroup.value = groupName
  }
}

function closeMenus() {
  showUserMenu.value = false
  openGroup.value = null
  showNotifications.value = false
  showRoleMenu.value = false
}

function toggleRoleMenu() {
  showRoleMenu.value = !showRoleMenu.value
}

async function handleRoleChange(newRole: 'ADMIN' | 'PRO' | 'USER') {
  if (changingRole.value || authStore.user?.role === newRole) {
    return
  }
  
  try {
    changingRole.value = true
    await changeMyRole(newRole)
    await authStore.fetchUser()
    showRoleMenu.value = false
  } catch (error: any) {
    console.error('Erro ao mudar role:', error)
    alert(error.message || 'Erro ao mudar tier')
  } finally {
    changingRole.value = false
  }
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value && notificationsStore.notifications.length === 0) {
    loadNotifications()
  }
}

async function loadNotifications() {
  try {
    await notificationsStore.loadNotifications({ limit: 20 })
  } catch (error) {
    console.error('Erro ao carregar notificações:', error)
  }
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.user-menu-group') && !target.closest('.nav-group') && !target.closest('.notifications-group') && !target.closest('.role-menu-group')) {
    closeMenus()
  }
}

const unreadCount = computed(() => notificationsStore.unreadCount)
const notifications = computed(() => notificationsStore.notifications)
const loadingNotifications = computed(() => notificationsStore.loading)

function formatDate(dateString: string | undefined): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Agora'
  if (diffMins < 60) return `${diffMins}min atrás`
  if (diffHours < 24) return `${diffHours}h atrás`
  if (diffDays < 7) return `${diffDays}d atrás`
  return date.toLocaleDateString('pt-BR')
}

function getNotificationIcon(type: string) {
  switch (type) {
    case 'ALERT_TRIGGERED':
      return AlertCircle
    case 'SUPPORT_RESPONSE':
      return MessageSquare
    case 'SUBSCRIPTION_UPDATE':
      return CreditCard
    default:
      return Bell
  }
}

function handleNotificationClick(notification: Notification) {
  showNotifications.value = false
  
  // Navegar para contexto baseado no tipo
  if (notification.data) {
    if (notification.type === 'ALERT_TRIGGERED' && notification.data.alert_id) {
      router.push('/alerts')
    } else if (notification.type === 'SUPPORT_RESPONSE' && notification.data.support_message_id) {
      router.push('/support')
    } else if (notification.type === 'SUBSCRIPTION_UPDATE') {
      router.push('/subscription')
    }
  }
  
  // Marcar como lida
  if (!notification.is_read) {
    notificationsStore.markAsRead(notification.id)
  }
}

async function markAsRead(notificationId: number, event: Event) {
  event.stopPropagation()
  try {
    await notificationsStore.markAsRead(notificationId)
  } catch (error) {
    console.error('Erro ao marcar como lida:', error)
  }
}

async function deleteNotification(notificationId: number, event: Event) {
  event.stopPropagation()
  try {
    await notificationsStore.deleteNotification(notificationId)
  } catch (error) {
    console.error('Erro ao deletar notificação:', error)
  }
}

async function markAllAsRead() {
  try {
    await notificationsStore.markAllAsRead()
  } catch (error) {
    console.error('Erro ao marcar todas como lidas:', error)
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Carregar notificações ao montar o componente
  if (authStore.isAuthenticated) {
    loadNotifications()
    // Atualizar notificações a cada 30 segundos
    notificationsInterval = setInterval(() => {
      loadNotifications()
    }, 30000)
  }
})

// Observar mudanças na autenticação
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    loadNotifications()
    if (notificationsInterval) {
      clearInterval(notificationsInterval)
    }
    notificationsInterval = setInterval(() => {
      loadNotifications()
    }, 30000)
  } else {
    if (notificationsInterval) {
      clearInterval(notificationsInterval)
      notificationsInterval = null
    }
    notificationsStore.reset()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (notificationsInterval) {
    clearInterval(notificationsInterval)
  }
})
</script>

<template>
  <header class="navbar">
    <div class="header-content">
      <div class="header-left">
        <div class="logo-small">
          <Coins :size="32" />
        </div>
        <h1>Finance App</h1>
      </div>
      
      <nav class="header-nav" aria-label="Navegação principal">
        <div class="nav-links">
          <div class="nav-group">
            <button @click="toggleGroup('investimentos')" class="nav-group-button" :class="{ active: openGroup === 'investimentos' || isGroupActive('investimentos') }">
              <span>Investimentos</span>
              <ChevronDown :size="16" class="chevron" :class="{ rotated: openGroup === 'investimentos' }" />
            </button>
            <div v-if="openGroup === 'investimentos'" class="nav-dropdown" @click.stop>
              <router-link to="/home" class="dropdown-item" @click="closeMenus">
                <BarChart :size="16" />
            <span>Dashboard</span>
          </router-link>
              <router-link to="/portfolio" class="dropdown-item" @click="closeMenus">
                <DollarSign :size="16" />
            <span>Portfólios</span>
          </router-link>
              <router-link to="/watchlist" class="dropdown-item" @click="closeMenus">
                <Eye :size="16" />
            <span>Watchlist</span>
          </router-link>
            </div>
          </div>
          
          <div class="nav-group">
            <button @click="toggleGroup('analise')" class="nav-group-button" :class="{ active: openGroup === 'analise' || isGroupActive('analise') }">
            <span>Análise</span>
              <ChevronDown :size="16" class="chevron" :class="{ rotated: openGroup === 'analise' }" />
            </button>
            <div v-if="openGroup === 'analise'" class="nav-dropdown" @click.stop>
              <router-link to="/market-analysis" class="dropdown-item" @click="closeMenus">
                <TrendingUp :size="16" />
                <span>Análise de Mercado</span>
          </router-link>
              <router-link v-if="isPro" to="/scanner" class="dropdown-item" @click="closeMenus">
                <Crown :size="16" />
            <span>Scanner (PRO)</span>
          </router-link>
            </div>
          </div>
          
          <div class="nav-group">
            <button @click="toggleGroup('alertas')" class="nav-group-button" :class="{ active: openGroup === 'alertas' || isGroupActive('alertas') }">
              <span>Alertas</span>
              <ChevronDown :size="16" class="chevron" :class="{ rotated: openGroup === 'alertas' }" />
            </button>
            <div v-if="openGroup === 'alertas'" class="nav-dropdown" @click.stop>
              <router-link to="/alerts" class="dropdown-item" @click="closeMenus">
                <Bell :size="16" />
                <span>Alertas</span>
              </router-link>
            </div>
          </div>
          
          <div class="nav-group">
            <button @click="toggleGroup('ajuda')" class="nav-group-button" :class="{ active: openGroup === 'ajuda' || isGroupActive('ajuda') }">
              <span>Ajuda</span>
              <ChevronDown :size="16" class="chevron" :class="{ rotated: openGroup === 'ajuda' }" />
            </button>
            <div v-if="openGroup === 'ajuda'" class="nav-dropdown" @click.stop>
              <router-link to="/support" class="dropdown-item" @click="closeMenus">
                <HelpCircle :size="16" />
            <span>Suporte</span>
          </router-link>
            </div>
          </div>
        </div>
      </nav>

      <div class="header-actions">
        <router-link 
          v-if="authStore.user?.role === 'ADMIN'"
          to="/admin"
          class="admin-link"
          title="Painel Administrativo"
        >
          <BarChart :size="16" />
          <span>Admin</span>
        </router-link>
        <div v-if="showRoleButton" class="role-menu-group">
          <button @click="toggleRoleMenu" class="role-button" :class="{ active: showRoleMenu }" title="Mudar Tier">
            <Crown :size="16" />
            <span>{{ authStore.user?.role }}</span>
            <ChevronDown :size="14" class="chevron" :class="{ rotated: showRoleMenu }" />
          </button>
          <div v-if="showRoleMenu" class="role-dropdown" @click.stop>
            <div class="role-dropdown-header">
              <Settings :size="16" />
              <span>Mudar Tier</span>
            </div>
            <div class="role-dropdown-divider"></div>
            <button 
              @click="handleRoleChange('ADMIN')" 
              class="role-dropdown-item" 
              :class="{ active: authStore.user?.role === 'ADMIN' }"
              :disabled="changingRole || authStore.user?.role === 'ADMIN'"
            >
              <Crown :size="16" />
              <span>ADMIN</span>
              <CheckCircle v-if="authStore.user?.role === 'ADMIN'" :size="14" />
            </button>
            <div v-if="!canChangeRole" class="role-dropdown-note">
              <span style="font-size: 12px; color: #94a3b8; padding: 8px 12px;">
                Apenas ADMIN pode mudar para outros tiers
              </span>
            </div>
            <button 
              v-if="canChangeRole"
              @click="handleRoleChange('PRO')" 
              class="role-dropdown-item" 
              :class="{ active: authStore.user?.role === 'PRO' }"
              :disabled="changingRole || authStore.user?.role === 'PRO'"
            >
              <Crown :size="16" />
              <span>PRO</span>
              <CheckCircle v-if="authStore.user?.role === 'PRO'" :size="14" />
            </button>
            <button 
              v-if="canChangeRole"
              @click="handleRoleChange('USER')" 
              class="role-dropdown-item" 
              :class="{ active: authStore.user?.role === 'USER' }"
              :disabled="changingRole || authStore.user?.role === 'USER'"
            >
              <User :size="16" />
              <span>USER</span>
              <CheckCircle v-if="authStore.user?.role === 'USER'" :size="14" />
            </button>
          </div>
        </div>
        <router-link 
          v-else-if="!isPro" 
          to="/subscription" 
          class="pro-link"
          title="Upgrade para PRO"
        >
          <Crown :size="16" />
          <span>PRO</span>
        </router-link>
        <div v-else class="pro-badge" title="Plano PRO Ativo">
          <Crown :size="16" />
          <span>PRO</span>
        </div>
        <div class="notifications-group">
          <button @click="toggleNotifications" class="notifications-button" :class="{ active: showNotifications }" title="Notificações">
            <Bell :size="20" />
            <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </button>
          <div v-if="showNotifications" class="notifications-dropdown" @click.stop>
            <div class="notifications-header">
              <h3>Notificações</h3>
              <div style="display: flex; gap: 8px; align-items: center;">
                <button 
                  v-if="unreadCount > 0" 
                  @click="markAllAsRead" 
                  class="mark-all-button" 
                  title="Marcar todas como lidas"
                >
                  <CheckCircle :size="16" />
                </button>
                <button @click="loadNotifications" class="refresh-button" :disabled="loadingNotifications" title="Atualizar">
                  <span v-if="loadingNotifications">...</span>
                  <span v-else>↻</span>
                </button>
              </div>
            </div>
            <div class="notifications-list">
              <div v-if="loadingNotifications && notifications.length === 0" class="notification-empty">
                Carregando...
              </div>
              <div v-else-if="notifications.length === 0" class="notification-empty">
                Nenhuma notificação
              </div>
              <div
                v-else
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="{ 'unread': !notification.is_read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-icon">
                  <component :is="getNotificationIcon(notification.type)" :size="16" />
                </div>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">{{ formatDate(notification.created_at) }}</div>
                </div>
                <div class="notification-actions" @click.stop>
                  <button 
                    v-if="!notification.is_read"
                    @click="markAsRead(notification.id, $event)"
                    class="action-button"
                    title="Marcar como lida"
                  >
                    <CheckCircle :size="14" />
                  </button>
                  <button 
                    @click="deleteNotification(notification.id, $event)"
                    class="action-button delete"
                    title="Deletar"
                  >
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="user-menu-group">
          <button @click="toggleUserMenu" class="user-info-button" :class="{ active: showUserMenu }">
          <div class="user-avatar">
            <User :size="20" />
          </div>
            <span class="user-name-short">{{ authStore.user?.username }}</span>
            <ChevronDown :size="16" class="chevron" :class="{ rotated: showUserMenu }" />
          </button>
          <div v-if="showUserMenu" class="user-dropdown-menu" @click.stop>
            <div class="user-dropdown-header">
              <div class="user-avatar-large">
                <User :size="24" />
              </div>
              <div class="user-dropdown-details">
            <span class="user-name">{{ authStore.user?.username }}</span>
            <span class="user-email">{{ authStore.user?.email }}</span>
          </div>
            </div>
            <div class="user-dropdown-divider"></div>
            <router-link to="/profile" class="user-dropdown-item" @click="closeMenus">
              <User :size="16" />
              <span>Perfil</span>
        </router-link>
            <button @click="() => { closeMenus(); handleLogout(); }" class="user-dropdown-item logout-item">
              <LogOut :size="16" />
              <span>Sair</span>
        </button>
          </div>
        </div>
        <button @click="toggleMobileMenu" class="mobile-menu-button">
          <Menu v-if="!showMobileMenu" :size="24" />
          <X v-else :size="24" />
        </button>
      </div>
    </div>

    <div v-if="showMobileMenu" class="mobile-menu">
      <nav class="mobile-nav" aria-label="Menu mobile">
        <router-link to="/home" class="mobile-nav-link" aria-label="Dashboard">
          <BarChart :size="20" />
          <span>Dashboard</span>
        </router-link>
        <router-link to="/portfolio" class="mobile-nav-link" aria-label="Portfólio">
          <DollarSign :size="20" />
          <span>Portfólio</span>
        </router-link>
        <router-link to="/watchlist" class="mobile-nav-link" aria-label="Watchlist">
          <Eye :size="20" />
          <span>Watchlist</span>
        </router-link>
        <router-link to="/alerts" class="mobile-nav-link" aria-label="Alertas">
          <Bell :size="20" />
          <span>Alertas</span>
        </router-link>
        <router-link to="/market-analysis" class="mobile-nav-link" aria-label="Análise de Mercado">
          <TrendingUp :size="20" />
          <span>Análise</span>
        </router-link>
        <router-link to="/scanner" class="mobile-nav-link" aria-label="Scanner (PRO)">
          <Crown :size="20" />
          <span>Scanner (PRO)</span>
        </router-link>
        <router-link to="/support" class="mobile-nav-link" aria-label="Suporte">
          <HelpCircle :size="20" />
          <span>Suporte</span>
        </router-link>
        <router-link 
          v-if="authStore.user?.role === 'ADMIN'"
          to="/admin"
          class="mobile-nav-link"
          aria-label="Painel Administrativo"
        >
          <BarChart :size="20" />
          <span>Admin</span>
        </router-link>
        <router-link 
          v-if="!isPro" 
          to="/subscription" 
          class="mobile-nav-link"
          aria-label="Upgrade para PRO"
        >
          <Crown :size="20" />
          <span>Upgrade PRO</span>
        </router-link>
        <router-link to="/profile" class="mobile-nav-link" aria-label="Perfil">
          <User :size="20" />
          <span>Perfil</span>
        </router-link>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
  min-height: 70px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-small {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-nav {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-links {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.nav-group {
  position: relative;
}

.nav-group-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
  border: none;
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
}

.nav-group-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.nav-group-button.active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
}

.chevron {
  transition: transform 0.2s;
}

.chevron.rotated {
  transform: rotate(180deg);
}

.nav-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  min-width: 200px;
  padding: 8px;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
  width: 100%;
  border: none;
  background: transparent;
}

.dropdown-item:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.dropdown-item.router-link-active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.nav-link.active,
.nav-link.router-link-active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pro-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.pro-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
}

.pro-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.admin-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.admin-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.notifications-group {
  position: relative;
}

.notifications-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  width: 40px;
  height: 40px;
}

.notifications-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.notifications-button.active {
  background: #e0f2fe;
  color: #3b82f6;
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ef4444;
  color: white;
  border-radius: 10px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  padding: 0 4px;
  border: 2px solid white;
}

.notifications-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  width: 360px;
  max-height: 500px;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  overflow: hidden;
}

.notifications-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.notifications-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.refresh-button {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 18px;
  transition: all 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background: #f1f5f9;
  color: #3b82f6;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notifications-list {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.notification-empty {
  padding: 32px 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.notification-item.unread {
  background: #f0f9ff;
  border-left: 3px solid #3b82f6;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item.unread:hover {
  background: #e0f2fe;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-message {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: #94a3b8;
}

.notification-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.action-button.delete:hover {
  background: #fee2e2;
  color: #dc2626;
}

.mark-all-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.mark-all-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.notifications-footer {
  padding: 12px 16px;
  border-top: 1px solid #e2e8f0;
  text-align: center;
}

.view-all-link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.view-all-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.user-menu-group {
  position: relative;
}

.user-info-button {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.user-info-button:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.user-info-button.active {
  background: #e2e8f0;
  border-color: #3b82f6;
}

.user-name-short {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  display: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  min-width: 240px;
  padding: 12px;
  z-index: 1000;
}

.user-dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  margin-bottom: 8px;
}

.user-avatar-large {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.user-dropdown-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.user-dropdown-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 8px 0;
}

.user-dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
}

.user-dropdown-item:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.user-dropdown-item.logout-item {
  color: #dc2626;
}

.user-dropdown-item.logout-item:hover {
  background: #fee2e2;
  color: #991b1b;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.2;
}

.user-email {
  font-size: 12px;
  color: #64748b;
  line-height: 1.2;
}

.logout-button {
  display: none;
}

.mobile-menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.mobile-menu-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.mobile-menu {
  display: none;
  border-top: 1px solid #e2e8f0;
  background: white;
  padding: 16px 24px;
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s;
}

.mobile-nav-link:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.mobile-nav-link.router-link-active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
}

@media (min-width: 769px) {
  .user-name-short {
    display: block;
  }
}

@media (max-width: 968px) {
  .header-nav {
    display: none;
  }

  .mobile-menu-button {
    display: flex;
  }

  .mobile-menu {
    display: block;
  }

  .user-info-button .user-details {
    display: none;
  }

  .user-name-short {
    display: block;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
    gap: 16px;
  }

  .header-left h1 {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .header-content {
    min-height: 60px;
  }

  .logo-small {
    display: none;
  }

  .header-left h1 {
    font-size: 18px;
  }

  .user-name-short {
    display: none;
  }

  .pro-link span,
  .pro-badge span,
  .admin-link span {
    display: none;
  }

  .notifications-dropdown {
    width: 320px;
    right: -20px;
  }
}

.role-menu-group {
  position: relative;
}

.role-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.role-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.role-button.active {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
}

.role-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  min-width: 200px;
  padding: 8px;
  z-index: 1000;
}

.role-dropdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.role-dropdown-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 4px 0;
}

.role-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  justify-content: space-between;
}

.role-dropdown-item:hover:not(:disabled) {
  background: #f1f5f9;
  color: #3b82f6;
}

.role-dropdown-item.active {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  color: white;
}

.role-dropdown-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .role-button span {
    display: none;
  }
}
</style>

