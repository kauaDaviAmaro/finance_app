import axios, { AxiosError } from 'axios'
import type { AxiosInstance } from 'axios'
import { isTokenExpired } from '../../utils/jwt'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      // Verifica se o token está expirado antes de enviar a requisição
      if (isTokenExpired(token)) {
        // Remove o token expirado
        localStorage.removeItem('token')
        // Redireciona para login se não estiver já na página de login
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login'
        }
        return Promise.reject(new ApiError(401, 'Token expirado'))
      }
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    if (error.response) {
      // Se receber 401 (não autorizado), o token pode estar expirado ou inválido
      if (error.response.status === 401) {
        const token = localStorage.getItem('token')
        if (token) {
          // Remove o token inválido
          localStorage.removeItem('token')
          // Redireciona para login se não estiver já na página de login
          if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
            window.location.href = '/login'
          }
        }
      }
      
      const message =
        (error.response.data as { detail?: string })?.detail ||
        error.response.statusText ||
        'Erro na requisição'
      throw new ApiError(error.response.status, message)
    } else if (error.request) {
      throw new ApiError(0, 'Erro de conexão. Verifique sua internet.')
    } else {
      throw new ApiError(0, error.message || 'Erro desconhecido')
    }
  }
)

