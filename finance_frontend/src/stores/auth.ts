import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api, type User, type LoginRequest, type RegisterRequest, ApiError } from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  function setUser(newUser: User | null) {
    user.value = newUser
  }

  async function login(credentials: LoginRequest): Promise<void> {
    try {
      const response = await api.login(credentials)
      setToken(response.access_token)
      await fetchUser()
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.message || 'Credenciais inválidas')
      }
      throw new Error('Erro ao fazer login. Tente novamente.')
    }
  }

  async function register(data: RegisterRequest): Promise<void> {
    try {
      await api.register(data)
      await login({ email: data.email, password: data.password })
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.message || 'Erro ao registrar')
      }
      throw new Error('Erro ao registrar. Tente novamente.')
    }
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return

    try {
      const userData = await api.getMe()
      setUser(userData)
    } catch (error) {
      logout()
      throw error
    }
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  async function initialize() {
    if (token.value) {
      try {
        await fetchUser()
      } catch (error) {
        logout()
      }
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
    initialize,
  }
})
