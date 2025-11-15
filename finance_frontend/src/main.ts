import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useNotificationsStore } from './stores/notifications'
import { registerServiceWorker } from './services/pushNotifications'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

async function initApp() {
  // Registrar service worker
  if ('serviceWorker' in navigator) {
    try {
      await registerServiceWorker()
      console.log('Service Worker registrado com sucesso')
    } catch (error) {
      console.error('Erro ao registrar Service Worker:', error)
    }
  }

  const authStore = useAuthStore()
  await authStore.initialize()
  
  // Inicializar push notifications se usuário estiver autenticado
  if (authStore.isAuthenticated) {
    const notificationsStore = useNotificationsStore()
    try {
      await notificationsStore.initializePush()
      // Carregar notificações iniciais
      await notificationsStore.loadNotifications({ limit: 20 })
    } catch (error) {
      console.error('Erro ao inicializar notificações:', error)
    }
  }
  
  app.mount('#app')
}

initApp()
