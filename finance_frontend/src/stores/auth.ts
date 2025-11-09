import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api, type User, type LoginRequest, type RegisterRequest, type UserUpdate, ApiError } from '../services/api/index'
import { isTokenValid } from '../utils/jwt'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => {
    if (!token.value) {
      return false
    }
    // Verifica se o token está válido (não expirado)
    if (!isTokenValid(token.value)) {
      // Se o token estiver expirado, remove-o
      setToken(null)
      return false
    }
    return true
  })

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

  async function updateProfile(update: UserUpdate): Promise<void> {
    try {
      await api.updateMe(update)
      await fetchUser()
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.message || 'Erro ao atualizar perfil')
      }
      throw new Error('Erro ao atualizar perfil. Tente novamente.')
    }
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  async function initialize() {
    if (token.value) {
      // Verifica se o token está válido antes de tentar buscar o usuário
      if (!isTokenValid(token.value)) {
        logout()
        return
      }
      try {
        await fetchUser()
      } catch {
        // Se houver erro ao buscar usuário, faz logout
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
    updateProfile,
    initialize,
  }
})
