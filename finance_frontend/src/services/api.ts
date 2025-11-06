import axios, { AxiosError } from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  full_name?: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  username: string
  full_name?: string
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
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

export interface HistoricalPrice {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TickerHistoricalData {
  ticker: string
  period: string
  data: HistoricalPrice[]
}

export interface TechnicalIndicator {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  macd?: number
  macd_signal?: number
  macd_histogram?: number
  stochastic_k?: number
  stochastic_d?: number
  atr?: number
  bb_lower?: number
  bb_middle?: number
  bb_upper?: number
  obv?: number
  rsi?: number
}

export interface TechnicalAnalysis {
  ticker: string
  period: string
  data: TechnicalIndicator[]
}

export interface Fundamentals {
  ticker: string
  pe_ratio?: number
  pb_ratio?: number
  dividend_yield?: number
  beta?: number
  sector?: string
  industry?: string
  market_cap?: number
}

export interface TickerRequest {
  ticker: string
  period?: string
}

export interface PortfolioItem {
  id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
  sold_price?: number
  sold_date?: string
  realized_pnl?: number
  unrealized_pnl?: number
  current_price?: number
  created_at: string
  updated_at?: string
}

export interface PortfolioSummary {
  total_invested: number
  total_realized_pnl: number
  total_unrealized_pnl: number
  positions: PortfolioItem[]
}

export interface PortfolioItemCreate {
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
}

export interface PortfolioItemUpdate {
  sold_price: number
  sold_date: string
}

export interface WatchlistItem {
  id: number
  ticker: string
  created_at: string
}

export interface WatchlistResponse {
  items: WatchlistItem[]
}

export interface Alert {
  id: number
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number
  is_active: boolean
  triggered_at?: string
  created_at: string
}

export interface AlertListResponse {
  alerts: Alert[]
}

export interface AlertCreate {
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number
}

export const api = {
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

  async getHistoricalData(ticker: string, period: string = '1y'): Promise<TickerHistoricalData> {
    const response = await apiClient.post<TickerHistoricalData>('/stocks/historical-data', {
      ticker,
      period,
    })
    return response.data
  },

  async getTechnicalAnalysis(ticker: string, period: string = '1y'): Promise<TechnicalAnalysis> {
    const response = await apiClient.post<TechnicalAnalysis>('/stocks/analysis', {
      ticker,
      period,
    })
    return response.data
  },

  async getFundamentals(ticker: string): Promise<Fundamentals> {
    const response = await apiClient.get<Fundamentals>(`/stocks/fundamentals/${ticker}`)
    return response.data
  },

  async getPortfolio(): Promise<PortfolioSummary> {
    const response = await apiClient.get<PortfolioSummary>('/portfolio')
    return response.data
  },

  async addPortfolioItem(item: PortfolioItemCreate): Promise<PortfolioItem> {
    const response = await apiClient.post<PortfolioItem>('/portfolio', item)
    return response.data
  },

  async sellPortfolioItem(itemId: number, update: PortfolioItemUpdate): Promise<PortfolioItem> {
    const response = await apiClient.patch<PortfolioItem>(`/portfolio/${itemId}/sell`, update)
    return response.data
  },

  async deletePortfolioItem(itemId: number): Promise<void> {
    await apiClient.delete(`/portfolio/${itemId}`)
  },

  async getWatchlist(): Promise<WatchlistResponse> {
    const response = await apiClient.get<WatchlistResponse>('/watchlist')
    return response.data
  },

  async addToWatchlist(ticker: string): Promise<WatchlistItem> {
    const response = await apiClient.post<WatchlistItem>('/watchlist', { ticker })
    return response.data
  },

  async removeFromWatchlist(ticker: string): Promise<void> {
    await apiClient.delete(`/watchlist/${ticker}`)
  },

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

export { ApiError }