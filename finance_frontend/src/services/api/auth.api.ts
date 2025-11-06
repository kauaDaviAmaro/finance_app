import { apiClient } from './apiClient'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from './types'

export const authApi = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials)
    return response.data
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data)
    return response.data
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },
}

