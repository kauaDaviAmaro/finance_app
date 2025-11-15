// Auth Types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
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
  role: 'ADMIN' | 'PRO' | 'USER'
  subscription_status?: string | null
  created_at?: string
  two_factor_enabled?: boolean
}

// Stock Types
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

// Portfolio Types
export interface Portfolio {
  id: number
  name: string
  category?: string | null
  description?: string | null
  created_at: string
  updated_at?: string | null
  item_count?: number
}

export interface PortfolioList {
  portfolios: Portfolio[]
}

export interface PortfolioCreate {
  name: string
  category?: string | null
  description?: string | null
}

export interface PortfolioUpdate {
  name?: string
  category?: string | null
  description?: string | null
}

export interface PortfolioItem {
  id: number
  portfolio_id: number
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
  portfolio_id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
}

export interface PortfolioItemUpdate {
  sold_price: number
  sold_date: string
}

// Watchlist Types
export interface WatchlistItem {
  id: number
  ticker: string
  created_at: string
}

export interface WatchlistResponse {
  items: WatchlistItem[]
}

// Alert Types
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

// Subscription Types
export interface SubscriptionStatus {
  role: 'ADMIN' | 'PRO' | 'USER'
  subscription_status: string | null
  is_pro: boolean
}

export interface CheckoutSessionResponse {
  url: string
  session_id: string
}

export interface PortalSessionResponse {
  url: string
}


// Profile Types
export interface UserUpdate {
  email?: string
  username?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}


// Scanner Types
export interface ScannerRow {
  ticker: string
  last_price: number | null
  rsi_14: number | null
  macd_h: number | null
  bb_upper: number | null
  bb_lower: number | null
  timestamp: string
}

export type ScannerSort = 'rsi_asc' | 'rsi_desc' | 'macd_desc'

