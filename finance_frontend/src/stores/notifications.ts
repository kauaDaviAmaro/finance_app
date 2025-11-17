import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationsApi, type Notification } from '../services/api/notifications.api'
import { initializePushNotifications } from '../services/pushNotifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pushEnabled = ref(false)

  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.is_read).length
  })

  const unreadNotifications = computed(() => {
    return notifications.value.filter(n => !n.is_read)
  })

  /**
   * Carregar notificações do servidor
   */
  async function loadNotifications(params?: {
    skip?: number
    limit?: number
    unread_only?: boolean
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await notificationsApi.getNotifications(params)
      notifications.value = response.notifications
      return response
    } catch (err: any) {
      error.value = err.message || 'Erro ao carregar notificações'
      console.error('Erro ao carregar notificações:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Marcar notificação como lida
   */
  async function markAsRead(notificationId: number) {
    try {
      await notificationsApi.markAsRead(notificationId)
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
    } catch (err: any) {
      error.value = err.message || 'Erro ao marcar notificação como lida'
      console.error('Erro ao marcar notificação como lida:', err)
      throw err
    }
  }

  /**
   * Marcar todas as notificações como lidas
   */
  async function markAllAsRead() {
    try {
      await notificationsApi.markAllAsRead()
      notifications.value.forEach(n => {
        n.is_read = true
      })
    } catch (err: any) {
      error.value = err.message || 'Erro ao marcar todas como lidas'
      console.error('Erro ao marcar todas como lidas:', err)
      throw err
    }
  }

  /**
   * Deletar notificação
   */
  async function deleteNotification(notificationId: number) {
    try {
      await notificationsApi.deleteNotification(notificationId)
      notifications.value = notifications.value.filter(n => n.id !== notificationId)
    } catch (err: any) {
      error.value = err.message || 'Erro ao deletar notificação'
      console.error('Erro ao deletar notificação:', err)
      throw err
    }
  }

  /**
   * Adicionar notificação localmente (para atualizações em tempo real)
   */
  function addNotification(notification: Notification) {
    // Adiciona no início da lista
    notifications.value.unshift(notification)
    // Limita a 100 notificações
    if (notifications.value.length > 100) {
      notifications.value = notifications.value.slice(0, 100)
    }
  }

  /**
   * Inicializar push notifications
   */
  async function initializePush() {
    try {
      const subscription = await initializePushNotifications()
      if (subscription) {
        // Registrar subscription no backend
        await notificationsApi.subscribe(subscription)
        pushEnabled.value = true
        return true
      }
      return false
    } catch (err: any) {
      console.error('Erro ao inicializar push notifications:', err)
      pushEnabled.value = false
      return false
    }
  }

  /**
   * Resetar store
   */
  function reset() {
    notifications.value = []
    loading.value = false
    error.value = null
    pushEnabled.value = false
  }

  return {
    // State
    notifications,
    loading,
    error,
    pushEnabled,
    
    // Getters
    unreadCount,
    unreadNotifications,
    
    // Actions
    loadNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    addNotification,
    initializePush,
    reset
  }
})





