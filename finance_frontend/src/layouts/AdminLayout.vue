<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { 
  LayoutDashboard, Users, Bell, Briefcase, Eye, 
  TrendingUp, BarChart3, LogOut, ArrowLeft, Menu, X 
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sidebarOpen = ref(true)
const mobileMenuOpen = ref(false)

const isAdmin = computed(() => authStore.user?.role === 'ADMIN')

const menuItems = [
  { name: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
  { name: 'Usuários', path: '/admin/users', icon: Users },
  { name: 'Alertas', path: '/admin/alerts', icon: Bell },
  { name: 'Portfólio', path: '/admin/portfolio', icon: Briefcase },
  { name: 'Watchlist', path: '/admin/watchlist', icon: Eye },
  { name: 'Ticker Prices', path: '/admin/ticker-prices', icon: TrendingUp },
  { name: 'Scan Results', path: '/admin/scan-results', icon: BarChart3 },
]

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function goToApp() {
  router.push('/home')
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function isActive(path: string) {
  if (path === '/admin/dashboard') {
    return route.path === '/admin' || route.path === '/admin/dashboard'
  }
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside :class="['sidebar', { 'sidebar-collapsed': !sidebarOpen }]">
      <div class="sidebar-header">
        <div class="logo">
          <BarChart3 :size="28" />
          <span v-if="sidebarOpen" class="logo-text">Admin Panel</span>
        </div>
        <button v-if="sidebarOpen" @click="toggleSidebar" class="sidebar-toggle" title="Recolher">
          <X :size="20" />
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: isActive(item.path) }]"
        >
          <component :is="item.icon" :size="20" />
          <span v-if="sidebarOpen" class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button @click="goToApp" class="footer-button">
          <ArrowLeft :size="18" />
          <span v-if="sidebarOpen">Voltar ao App</span>
        </button>
        <button @click="handleLogout" class="footer-button logout">
          <LogOut :size="18" />
          <span v-if="sidebarOpen">Sair</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="main-content" :class="{ 'sidebar-open': sidebarOpen }">
      <!-- Header -->
      <header class="admin-header">
        <div class="header-left">
          <button @click="toggleSidebar" class="menu-button">
            <Menu :size="24" />
          </button>
          <h1 class="page-title">{{ route.meta.title || 'Admin' }}</h1>
        </div>
        <div class="header-right">
          <div class="user-info">
            <span class="user-name">{{ authStore.user?.username }}</span>
            <span class="user-role">ADMIN</span>
          </div>
        </div>
      </header>

      <!-- Content Area -->
      <main class="content-area">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </main>
    </div>

    <!-- Mobile Menu Overlay -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="toggleMobileMenu">
      <aside class="mobile-sidebar" @click.stop>
        <div class="mobile-header">
          <h2>Admin Panel</h2>
          <button @click="toggleMobileMenu" class="close-button">
            <X :size="24" />
          </button>
        </div>
        <nav class="mobile-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            :class="['mobile-nav-item', { active: isActive(item.path) }]"
            @click="toggleMobileMenu"
          >
            <component :is="item.icon" :size="20" />
            <span>{{ item.name }}</span>
          </router-link>
        </nav>
        <div class="mobile-footer">
          <button @click="goToApp" class="mobile-footer-button">
            <ArrowLeft :size="18" />
            <span>Voltar ao App</span>
          </button>
          <button @click="handleLogout" class="mobile-footer-button logout">
            <LogOut :size="18" />
            <span>Sair</span>
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

/* Sidebar */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 260px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  z-index: 1000;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-collapsed {
  width: 80px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
}

.sidebar-toggle {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
}

.footer-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.footer-button.logout {
  background: rgba(239, 68, 68, 0.2);
}

.footer-button.logout:hover {
  background: rgba(239, 68, 68, 0.3);
}

/* Main Content */
.main-content {
  margin-left: 260px;
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
  min-height: 100vh;
}

.main-content.sidebar-open {
  margin-left: 260px;
}

.admin-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-button {
  display: none;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.menu-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.user-role {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
}

.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* Mobile */
.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000;
}

.mobile-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 280px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.3);
}

.mobile-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.close-button {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
}

.mobile-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.mobile-footer {
  padding: 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-footer-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
}

.mobile-footer-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.mobile-footer-button.logout {
  background: rgba(239, 68, 68, 0.2);
}

.mobile-footer-button.logout:hover {
  background: rgba(239, 68, 68, 0.3);
}

@media (max-width: 968px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .main-content {
    margin-left: 0;
  }

  .menu-button {
    display: flex;
  }

  .mobile-overlay {
    display: block;
  }
}

@media (max-width: 640px) {
  .content-area {
    padding: 16px;
  }

  .page-title {
    font-size: 20px;
  }
}
</style>

