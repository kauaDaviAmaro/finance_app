import { apiClient } from './apiClient'
import type { User, UserUpdate, ChangePasswordRequest } from './types'

export const userApi = {
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },

  async updateMe(payload: UserUpdate): Promise<User> {
    const response = await apiClient.put<User>('/auth/me', payload)
    return response.data
  },

  async changePassword(payload: ChangePasswordRequest): Promise<void> {
    await apiClient.post('/auth/change-password', payload)
  },
}







