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
export { subscriptionApi } from './subscription.api'
export { userApi } from './user.api'
export { notificationsApi } from './notifications.api'
export { backtestingApi } from './backtesting.api'
export { riskApi } from './risk.api'

// Unified API object for backward compatibility
import { authApi } from './auth.api'
import { stocksApi } from './stocks.api'
import { portfolioApi } from './portfolio.api'
import { watchlistApi } from './watchlist.api'
import { alertsApi } from './alerts.api'
import { subscriptionApi } from './subscription.api'
import { userApi } from './user.api'
import { notificationsApi } from './notifications.api'
import { backtestingApi } from './backtesting.api'

export const api = {
  // Auth methods
  login: authApi.login,
  register: authApi.register,
  getMe: authApi.getMe,
  
  // Stock methods
  getHistoricalData: stocksApi.getHistoricalData,
  getTechnicalAnalysis: stocksApi.getTechnicalAnalysis,
  getFundamentals: stocksApi.getFundamentals,
  getMostSearchedTickers: stocksApi.getMostSearchedTickers,
  compareTickers: stocksApi.compareTickers,
  getFinancialStatements: stocksApi.getFinancialStatements,
  
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
  
  // Subscription methods
  createCheckoutSession: subscriptionApi.createCheckoutSession,
  getSubscriptionStatus: subscriptionApi.getSubscriptionStatus,
  createPortalSession: subscriptionApi.createPortalSession,

  // User methods
  updateMe: userApi.updateMe,
  changePassword: userApi.changePassword,
  
  // Notification methods
  getNotifications: notificationsApi.getNotifications,
  markAsRead: notificationsApi.markAsRead,
  markAllAsRead: notificationsApi.markAllAsRead,
  deleteNotification: notificationsApi.deleteNotification,
  
  // Backtesting methods
  getStrategies: backtestingApi.getStrategies,
  getStrategy: backtestingApi.getStrategy,
  createStrategy: backtestingApi.createStrategy,
  updateStrategy: backtestingApi.updateStrategy,
  deleteStrategy: backtestingApi.deleteStrategy,
  runBacktest: backtestingApi.runBacktest,
  getBacktestResult: backtestingApi.getBacktestResult,
  getBacktestResults: backtestingApi.getBacktestResults,
  compareStrategies: backtestingApi.compareStrategies,
  startPaperTrading: backtestingApi.startPaperTrading,
  getPaperTradingStatus: backtestingApi.getPaperTradingStatus,
  stopPaperTrading: backtestingApi.stopPaperTrading,
  pausePaperTrading: backtestingApi.pausePaperTrading,
  getPaperTradingPositions: backtestingApi.getPaperTradingPositions,
  getPaperTradingHistory: backtestingApi.getPaperTradingHistory,
  getPaperTradingDetail: backtestingApi.getPaperTradingDetail,
  getPaperTradingAllPositions: backtestingApi.getPaperTradingAllPositions,
  getActivePaperTrading: backtestingApi.getActivePaperTrading,
  
  // Advanced Analysis methods (PRO only)
  getAdvancedAnalysis: stocksApi.getAdvancedAnalysis,
  saveElliottAnnotations: stocksApi.saveElliottAnnotations,
  getElliottAnnotations: stocksApi.getElliottAnnotations,
  deleteElliottAnnotations: stocksApi.deleteElliottAnnotations,
}

