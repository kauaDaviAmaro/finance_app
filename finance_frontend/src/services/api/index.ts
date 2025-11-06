// Export all types
export * from './types'

// Export API client and error
export { apiClient, ApiError } from './apiClient'

// Export API modules
export { authApi } from './auth.api'
export { stocksApi } from './stocks.api'
export { portfolioApi } from './portfolio.api'
export { watchlistApi } from './watchlist.api'
export { alertsApi } from './alerts.api'

// Unified API object for backward compatibility
import { authApi } from './auth.api'
import { stocksApi } from './stocks.api'
import { portfolioApi } from './portfolio.api'
import { watchlistApi } from './watchlist.api'
import { alertsApi } from './alerts.api'

export const api = {
  // Auth methods
  login: authApi.login,
  register: authApi.register,
  getMe: authApi.getMe,
  
  // Stock methods
  getHistoricalData: stocksApi.getHistoricalData,
  getTechnicalAnalysis: stocksApi.getTechnicalAnalysis,
  getFundamentals: stocksApi.getFundamentals,
  
  // Portfolio methods
  getPortfolio: portfolioApi.getPortfolio,
  addPortfolioItem: portfolioApi.addPortfolioItem,
  sellPortfolioItem: portfolioApi.sellPortfolioItem,
  deletePortfolioItem: portfolioApi.deletePortfolioItem,
  
  // Watchlist methods
  getWatchlist: watchlistApi.getWatchlist,
  addToWatchlist: watchlistApi.addToWatchlist,
  removeFromWatchlist: watchlistApi.removeFromWatchlist,
  
  // Alert methods
  getAlerts: alertsApi.getAlerts,
  createAlert: alertsApi.createAlert,
  toggleAlert: alertsApi.toggleAlert,
  deleteAlert: alertsApi.deleteAlert,
}

