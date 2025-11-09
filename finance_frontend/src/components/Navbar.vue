<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Coins, BarChart, Eye, Bell, TrendingUp, LogOut, User, Menu, X, DollarSign, Crown } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const showMobileMenu = ref(false)

const isPro = computed(() => {
  return authStore.user?.role === 'PRO' || authStore.user?.role === 'ADMIN'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function toggleMobileMenu() {
  showMobileMenu.value = !showMobileMenu.value
}
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
          <router-link to="/home" class="nav-link" aria-label="Dashboard">
            <BarChart :size="18" />
            <span>Dashboard</span>
          </router-link>
          <router-link to="/portfolio" class="nav-link" aria-label="Portfólio">
            <DollarSign :size="18" />
            <span>Portfólio</span>
          </router-link>
          <router-link to="/watchlist" class="nav-link" aria-label="Watchlist">
            <Eye :size="18" />
            <span>Watchlist</span>
          </router-link>
          <router-link to="/alerts" class="nav-link" aria-label="Alertas">
            <Bell :size="18" />
            <span>Alertas</span>
          </router-link>
          <router-link to="/market-analysis" class="nav-link" aria-label="Análise de Mercado">
            <TrendingUp :size="18" />
            <span>Análise</span>
          </router-link>
          <router-link to="/scanner" class="nav-link" aria-label="Scanner (PRO)">
            <Crown :size="18" />
            <span>Scanner (PRO)</span>
          </router-link>
        </div>
      </nav>

      <div class="header-actions">
        <router-link 
          v-if="!isPro" 
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
        <router-link to="/profile" class="user-info" aria-label="Perfil">
          <div class="user-avatar">
            <User :size="20" />
          </div>
          <div class="user-details">
            <span class="user-name">{{ authStore.user?.full_name || authStore.user?.username }}</span>
            <span class="user-email">{{ authStore.user?.email }}</span>
          </div>
        </router-link>
        <button @click="handleLogout" class="logout-button" title="Sair">
          <LogOut :size="18" />
          <span class="logout-text">Sair</span>
        </button>
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

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  background: #fecaca;
  transform: translateY(-1px);
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

  .user-info {
    display: none;
  }

  .logout-text {
    display: none;
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
}
</style>

