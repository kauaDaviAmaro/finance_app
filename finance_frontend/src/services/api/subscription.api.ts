import { apiClient } from './apiClient'
import type { 
  SubscriptionStatus, 
  CheckoutSessionResponse, 
  PortalSessionResponse 
} from './types'

export const subscriptionApi = {
  async createCheckoutSession(): Promise<CheckoutSessionResponse> {
    const response = await apiClient.post<CheckoutSessionResponse>(
      '/subscription/create-checkout-session'
    )
    return response.data
  },

  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    const response = await apiClient.get<SubscriptionStatus>(
      '/subscription/status'
    )
    return response.data
  },

  async createPortalSession(): Promise<PortalSessionResponse> {
    const response = await apiClient.post<PortalSessionResponse>(
      '/subscription/cancel'
    )
    return response.data
  },
}









