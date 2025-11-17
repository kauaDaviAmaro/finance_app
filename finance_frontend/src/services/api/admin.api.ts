import { apiClient, ApiError } from './apiClient'

// ============================================================================
// TYPES
// ============================================================================

export interface AdminStats {
  total_users: number
  active_users: number
  pro_users: number
  admin_users: number
  total_alerts: number
  active_alerts: number
  total_portfolios: number
  total_portfolio_items: number
  total_watchlist_items: number
  total_ticker_prices: number
  total_scan_results: number
  total_support_messages: number
  pending_support_messages: number
  users_by_role: Record<string, number>
  alerts_by_type: Record<string, number>
  users_over_time: Record<string, number>
}

export interface UserAdmin {
  id: number
  email: string
  username: string
  is_active: boolean
  is_verified: boolean
  role: 'ADMIN' | 'PRO' | 'USER'
  stripe_customer_id?: string | null
  subscription_status?: string | null
  created_at: string
  updated_at?: string | null
}

export interface UserAdminCreate {
  email: string
  username: string
  password: string
  is_active?: boolean
  is_verified?: boolean
  role?: 'ADMIN' | 'PRO' | 'USER'
  stripe_customer_id?: string | null
  subscription_status?: string | null
}

export interface UserAdminUpdate {
  email?: string
  username?: string
  password?: string
  is_active?: boolean
  is_verified?: boolean
  role?: 'ADMIN' | 'PRO' | 'USER'
  stripe_customer_id?: string | null
  subscription_status?: string | null
}

export interface AlertAdmin {
  id: number
  user_id: number
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number | null
  is_active: boolean
  triggered_at?: string | null
  created_at: string
}

export interface AlertAdminCreate {
  user_id: number
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number | null
  is_active?: boolean
}

export interface AlertAdminUpdate {
  user_id?: number
  ticker?: string
  indicator_type?: string
  condition?: string
  threshold_value?: number | null
  is_active?: boolean
  triggered_at?: string | null
}

export interface PortfolioAdmin {
  id: number
  user_id: number
  name: string
  category?: string | null
  description?: string | null
  created_at: string
  updated_at?: string | null
  item_count?: number
}

export interface PortfolioAdminCreate {
  user_id: number
  name: string
  category?: string | null
  description?: string | null
}

export interface PortfolioAdminUpdate {
  user_id?: number
  name?: string
  category?: string | null
  description?: string | null
}

export interface PortfolioItemAdmin {
  id: number
  user_id: number
  portfolio_id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
  sold_price?: number | null
  sold_date?: string | null
  created_at: string
  updated_at?: string | null
}

export interface PortfolioItemAdminCreate {
  user_id: number
  portfolio_id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
  sold_price?: number | null
  sold_date?: string | null
}

export interface PortfolioItemAdminUpdate {
  user_id?: number
  portfolio_id?: number
  ticker?: string
  quantity?: number
  purchase_price?: number
  purchase_date?: string
  sold_price?: number | null
  sold_date?: string | null
}

export interface WatchlistItemAdmin {
  id: number
  user_id: number
  ticker: string
  created_at: string
}

export interface WatchlistItemAdminCreate {
  user_id: number
  ticker: string
}

export interface WatchlistItemAdminUpdate {
  user_id?: number
  ticker?: string
}

export interface TickerPriceAdmin {
  ticker: string
  last_price: number
  timestamp: string
}

export interface TickerPriceAdminCreate {
  ticker: string
  last_price: number
}

export interface TickerPriceAdminUpdate {
  last_price?: number
  timestamp?: string
}

export interface DailyScanResultAdmin {
  ticker: string
  last_price: number
  rsi_14?: number | null
  macd_h?: number | null
  bb_upper?: number | null
  bb_lower?: number | null
  timestamp: string
}

export interface DailyScanResultAdminCreate {
  ticker: string
  last_price: number
  rsi_14?: number | null
  macd_h?: number | null
  bb_upper?: number | null
  bb_lower?: number | null
}

export interface DailyScanResultAdminUpdate {
  last_price?: number
  rsi_14?: number | null
  macd_h?: number | null
  bb_upper?: number | null
  bb_lower?: number | null
  timestamp?: string
}

// ============================================================================
// STATS
// ============================================================================

export async function getAdminStats(): Promise<AdminStats> {
  try {
    const response = await apiClient.get<AdminStats>('/admin/stats')
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar estatísticas')
  }
}

// ============================================================================
// USERS
// ============================================================================

export async function getUsers(skip = 0, limit = 100): Promise<UserAdmin[]> {
  try {
    const response = await apiClient.get<UserAdmin[]>('/admin/users', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar usuários')
  }
}

export async function getUser(id: number): Promise<UserAdmin> {
  try {
    const response = await apiClient.get<UserAdmin>(`/admin/users/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar usuário')
  }
}

export interface UserDetails {
  user: UserAdmin
  portfolios: PortfolioAdmin[]
  portfolio_items: PortfolioItemAdmin[]
  alerts: AlertAdmin[]
  watchlist_items: WatchlistItemAdmin[]
  support_messages: SupportMessageAdmin[]
}

export async function getUserDetails(id: number): Promise<UserDetails> {
  try {
    const response = await apiClient.get<UserDetails>(`/admin/users/${id}/details`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar detalhes do usuário')
  }
}

export async function createUser(data: UserAdminCreate): Promise<UserAdmin> {
  try {
    const response = await apiClient.post<UserAdmin>('/admin/users', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar usuário')
  }
}

export async function updateUser(id: number, data: UserAdminUpdate): Promise<UserAdmin> {
  try {
    const response = await apiClient.put<UserAdmin>(`/admin/users/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar usuário')
  }
}

export async function deleteUser(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/users/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar usuário')
  }
}

export async function changeMyRole(role: 'ADMIN' | 'PRO' | 'USER'): Promise<UserAdmin> {
  try {
    const response = await apiClient.post<UserAdmin>('/admin/change-my-role', { role })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao mudar role')
  }
}

// ============================================================================
// ALERTS
// ============================================================================

export async function getAlerts(skip = 0, limit = 100): Promise<AlertAdmin[]> {
  try {
    const response = await apiClient.get<AlertAdmin[]>('/admin/alerts', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar alertas')
  }
}

export async function getAlert(id: number): Promise<AlertAdmin> {
  try {
    const response = await apiClient.get<AlertAdmin>(`/admin/alerts/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar alerta')
  }
}

export async function createAlert(data: AlertAdminCreate): Promise<AlertAdmin> {
  try {
    const response = await apiClient.post<AlertAdmin>('/admin/alerts', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar alerta')
  }
}

export async function updateAlert(id: number, data: AlertAdminUpdate): Promise<AlertAdmin> {
  try {
    const response = await apiClient.put<AlertAdmin>(`/admin/alerts/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar alerta')
  }
}

export async function deleteAlert(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/alerts/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar alerta')
  }
}

// ============================================================================
// PORTFOLIOS
// ============================================================================

export async function getPortfolios(skip = 0, limit = 100, userId?: number): Promise<PortfolioAdmin[]> {
  try {
    const params: any = { skip, limit }
    if (userId) {
      params.user_id = userId
    }
    const response = await apiClient.get<PortfolioAdmin[]>('/admin/portfolios', { params })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar portfolios')
  }
}

export async function getPortfolio(id: number): Promise<PortfolioAdmin> {
  try {
    const response = await apiClient.get<PortfolioAdmin>(`/admin/portfolios/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar portfolio')
  }
}

export async function createPortfolio(data: PortfolioAdminCreate): Promise<PortfolioAdmin> {
  try {
    const response = await apiClient.post<PortfolioAdmin>('/admin/portfolios', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar portfolio')
  }
}

export async function updatePortfolio(id: number, data: PortfolioAdminUpdate): Promise<PortfolioAdmin> {
  try {
    const response = await apiClient.put<PortfolioAdmin>(`/admin/portfolios/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar portfolio')
  }
}

export async function deletePortfolio(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/portfolios/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar portfolio')
  }
}

// ============================================================================
// PORTFOLIO ITEMS
// ============================================================================

export async function getPortfolioItems(skip = 0, limit = 100): Promise<PortfolioItemAdmin[]> {
  try {
    const response = await apiClient.get<PortfolioItemAdmin[]>('/admin/portfolio', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar itens de portfólio')
  }
}

export async function getPortfolioItem(id: number): Promise<PortfolioItemAdmin> {
  try {
    const response = await apiClient.get<PortfolioItemAdmin>(`/admin/portfolio/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar item de portfólio')
  }
}

export async function createPortfolioItem(data: PortfolioItemAdminCreate): Promise<PortfolioItemAdmin> {
  try {
    const response = await apiClient.post<PortfolioItemAdmin>('/admin/portfolio', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar item de portfólio')
  }
}

export async function updatePortfolioItem(id: number, data: PortfolioItemAdminUpdate): Promise<PortfolioItemAdmin> {
  try {
    const response = await apiClient.put<PortfolioItemAdmin>(`/admin/portfolio/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar item de portfólio')
  }
}

export async function deletePortfolioItem(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/portfolio/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar item de portfólio')
  }
}

// ============================================================================
// WATCHLIST
// ============================================================================

export async function getWatchlistItems(skip = 0, limit = 100): Promise<WatchlistItemAdmin[]> {
  try {
    const response = await apiClient.get<WatchlistItemAdmin[]>('/admin/watchlist', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar itens de watchlist')
  }
}

export async function getWatchlistItem(id: number): Promise<WatchlistItemAdmin> {
  try {
    const response = await apiClient.get<WatchlistItemAdmin>(`/admin/watchlist/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar item de watchlist')
  }
}

export async function createWatchlistItem(data: WatchlistItemAdminCreate): Promise<WatchlistItemAdmin> {
  try {
    const response = await apiClient.post<WatchlistItemAdmin>('/admin/watchlist', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar item de watchlist')
  }
}

export async function updateWatchlistItem(id: number, data: WatchlistItemAdminUpdate): Promise<WatchlistItemAdmin> {
  try {
    const response = await apiClient.put<WatchlistItemAdmin>(`/admin/watchlist/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar item de watchlist')
  }
}

export async function deleteWatchlistItem(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/watchlist/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar item de watchlist')
  }
}

// ============================================================================
// TICKER PRICES
// ============================================================================

export async function getTickerPrices(skip = 0, limit = 100): Promise<TickerPriceAdmin[]> {
  try {
    const response = await apiClient.get<TickerPriceAdmin[]>('/admin/ticker-prices', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar preços de tickers')
  }
}

export async function getTickerPrice(ticker: string): Promise<TickerPriceAdmin> {
  try {
    const response = await apiClient.get<TickerPriceAdmin>(`/admin/ticker-prices/${ticker}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar preço de ticker')
  }
}

export async function createTickerPrice(data: TickerPriceAdminCreate): Promise<TickerPriceAdmin> {
  try {
    const response = await apiClient.post<TickerPriceAdmin>('/admin/ticker-prices', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar preço de ticker')
  }
}

export async function updateTickerPrice(ticker: string, data: TickerPriceAdminUpdate): Promise<TickerPriceAdmin> {
  try {
    const response = await apiClient.put<TickerPriceAdmin>(`/admin/ticker-prices/${ticker}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar preço de ticker')
  }
}

export async function deleteTickerPrice(ticker: string): Promise<void> {
  try {
    await apiClient.delete(`/admin/ticker-prices/${ticker}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar preço de ticker')
  }
}

// ============================================================================
// SCAN RESULTS
// ============================================================================

export async function getScanResults(skip = 0, limit = 100): Promise<DailyScanResultAdmin[]> {
  try {
    const response = await apiClient.get<DailyScanResultAdmin[]>('/admin/scan-results', {
      params: { skip, limit }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar resultados de scan')
  }
}

export async function getScanResult(ticker: string): Promise<DailyScanResultAdmin> {
  try {
    const response = await apiClient.get<DailyScanResultAdmin>(`/admin/scan-results/${ticker}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar resultado de scan')
  }
}

export async function createScanResult(data: DailyScanResultAdminCreate): Promise<DailyScanResultAdmin> {
  try {
    const response = await apiClient.post<DailyScanResultAdmin>('/admin/scan-results', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao criar resultado de scan')
  }
}

export async function updateScanResult(ticker: string, data: DailyScanResultAdminUpdate): Promise<DailyScanResultAdmin> {
  try {
    const response = await apiClient.put<DailyScanResultAdmin>(`/admin/scan-results/${ticker}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar resultado de scan')
  }
}

export async function deleteScanResult(ticker: string): Promise<void> {
  try {
    await apiClient.delete(`/admin/scan-results/${ticker}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar resultado de scan')
  }
}

// ============================================================================
// SUPPORT MESSAGES
// ============================================================================

export interface SupportMessageAdmin {
  id: number
  user_id?: number | null
  email: string
  category: string
  subject: string
  message: string
  status: string
  admin_response?: string | null
  responded_at?: string | null
  responded_by?: number | null
  created_at: string
  updated_at?: string | null
}

export interface SupportMessageAdminCreate {
  user_id?: number | null
  email: string
  category: string
  subject: string
  message: string
}

export interface SupportMessageAdminUpdate {
  status?: string
  admin_response?: string | null
  responded_by?: number | null
}

export async function getSupportMessages(skip = 0, limit = 100, status?: string): Promise<SupportMessageAdmin[]> {
  try {
    const params: any = { skip, limit }
    if (status) params.status = status
    const response = await apiClient.get<SupportMessageAdmin[]>('/admin/support', { params })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar mensagens de suporte')
  }
}

export async function getSupportMessage(id: number): Promise<SupportMessageAdmin> {
  try {
    const response = await apiClient.get<SupportMessageAdmin>(`/admin/support/${id}`)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao buscar mensagem de suporte')
  }
}

export async function updateSupportMessage(id: number, data: SupportMessageAdminUpdate): Promise<SupportMessageAdmin> {
  try {
    const response = await apiClient.put<SupportMessageAdmin>(`/admin/support/${id}`, data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao atualizar mensagem de suporte')
  }
}

export async function deleteSupportMessage(id: number): Promise<void> {
  try {
    await apiClient.delete(`/admin/support/${id}`)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao deletar mensagem de suporte')
  }
}

// ============================================================================
// SCANNER
// ============================================================================

export interface ScanStartResponse {
  message: string
  task_id?: string | null
  status: string
}

export async function startScanner(asyncMode: boolean = true): Promise<ScanStartResponse> {
  try {
    const response = await apiClient.post<ScanStartResponse>('/admin/scanner/start', null, {
      params: { async_mode: asyncMode }
    })
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao iniciar scanner')
  }
}

