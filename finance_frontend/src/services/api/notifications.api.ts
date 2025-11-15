import { apiClient } from './apiClient'
import type { PushSubscriptionData } from '../pushNotifications'

export interface Notification {
  id: number
  user_id: number
  type: string
  title: string
  message: string
  data: Record<string, any> | null
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  unread_count: number
}

export interface PushSubscriptionOut {
  id: number
  user_id: number
  endpoint: string
  created_at: string
}

export const notificationsApi = {
  /**
   * Registrar subscription de push notification
   */
  async subscribe(subscription: PushSubscriptionData): Promise<PushSubscriptionOut> {
    const response = await apiClient.post<PushSubscriptionOut>('/notifications/subscribe', subscription)
    return response.data
  },

  /**
   * Listar notificações do usuário
   */
  async getNotifications(params?: {
    skip?: number
    limit?: number
    unread_only?: boolean
  }): Promise<NotificationListResponse> {
    const response = await apiClient.get<NotificationListResponse>('/notifications', { params })
    return response.data
  },

  /**
   * Obter uma notificação específica
   */
  async getNotification(notificationId: number): Promise<Notification> {
    const response = await apiClient.get<Notification>(`/notifications/${notificationId}`)
    return response.data
  },

  /**
   * Marcar notificação como lida
   */
  async markAsRead(notificationId: number): Promise<void> {
    await apiClient.patch(`/notifications/${notificationId}/read`)
  },

  /**
   * Marcar todas as notificações como lidas
   */
  async markAllAsRead(): Promise<{ message: string }> {
    const response = await apiClient.patch<{ message: string }>('/notifications/read-all')
    return response.data
  },

  /**
   * Deletar notificação
   */
  async deleteNotification(notificationId: number): Promise<void> {
    await apiClient.delete(`/notifications/${notificationId}`)
  }
}


