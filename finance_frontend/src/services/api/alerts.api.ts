import { apiClient } from './apiClient'
import type { AlertListResponse, Alert, AlertCreate } from './types'

export const alertsApi = {
  async getAlerts(): Promise<AlertListResponse> {
    const response = await apiClient.get<AlertListResponse>('/alerts')
    return response.data
  },

  async createAlert(alert: AlertCreate): Promise<Alert> {
    const response = await apiClient.post<Alert>('/alerts', alert)
    return response.data
  },

  async toggleAlert(alertId: number): Promise<Alert> {
    const response = await apiClient.patch<Alert>(`/alerts/${alertId}/toggle`)
    return response.data
  },

  async deleteAlert(alertId: number): Promise<void> {
    await apiClient.delete(`/alerts/${alertId}`)
  },
}

