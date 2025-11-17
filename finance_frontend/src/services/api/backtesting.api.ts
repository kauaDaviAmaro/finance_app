import { apiClient } from './apiClient'
import type {
  Strategy,
  StrategyCreate,
  StrategyCreateJSON,
  StrategyUpdate,
  StrategyCondition,
  BacktestRunRequest,
  Backtest,
  BacktestResultDetail,
  BacktestCompareRequest,
  BacktestCompareResult,
  PaperTradeStartRequest,
  PaperTrade,
  PaperTradeStatusOut,
  PaperTradePosition
} from './types'

export const backtestingApi = {
  // Strategy CRUD
  async getStrategies(): Promise<Strategy[]> {
    const response = await apiClient.get<Strategy[]>('/backtesting/strategies')
    return response.data
  },

  async getStrategy(strategyId: number): Promise<Strategy> {
    const response = await apiClient.get<Strategy>(`/backtesting/strategies/${strategyId}`)
    return response.data
  },

  async createStrategy(data: StrategyCreate): Promise<Strategy> {
    const response = await apiClient.post<Strategy>('/backtesting/strategies', data)
    return response.data
  },

  async createStrategyJSON(data: StrategyCreateJSON): Promise<Strategy> {
    const response = await apiClient.post<Strategy>('/backtesting/strategies/json', data)
    return response.data
  },

  async updateStrategy(strategyId: number, data: StrategyUpdate): Promise<Strategy> {
    const response = await apiClient.put<Strategy>(`/backtesting/strategies/${strategyId}`, data)
    return response.data
  },

  async deleteStrategy(strategyId: number): Promise<void> {
    await apiClient.delete(`/backtesting/strategies/${strategyId}`)
  },

  // Backtest
  async runBacktest(data: BacktestRunRequest): Promise<Backtest> {
    const response = await apiClient.post<Backtest>('/backtesting/run', data)
    return response.data
  },

  async getBacktestResult(backtestId: number): Promise<BacktestResultDetail> {
    const response = await apiClient.get<BacktestResultDetail>(`/backtesting/results/${backtestId}`)
    return response.data
  },

  async getBacktestResults(limit?: number): Promise<Backtest[]> {
    const params = limit ? `?limit=${limit}` : ''
    const response = await apiClient.get<Backtest[]>(`/backtesting/results${params}`)
    return response.data
  },

  async compareStrategies(data: BacktestCompareRequest): Promise<BacktestCompareResult> {
    const response = await apiClient.post<BacktestCompareResult>('/backtesting/compare', data)
    return response.data
  },

  // Paper Trading (PRO only)
  async startPaperTrading(data: PaperTradeStartRequest): Promise<PaperTrade> {
    const response = await apiClient.post<PaperTrade>('/backtesting/paper-trading/start', data)
    return response.data
  },

  async getPaperTradingStatus(ticker: string): Promise<PaperTradeStatusOut> {
    const response = await apiClient.get<PaperTradeStatusOut>(`/backtesting/paper-trading?ticker=${ticker}`)
    return response.data
  },

  async stopPaperTrading(paperTradeId: number): Promise<PaperTrade> {
    const response = await apiClient.post<PaperTrade>(`/backtesting/paper-trading/stop?paper_trade_id=${paperTradeId}`, {})
    return response.data
  },

  async pausePaperTrading(paperTradeId: number): Promise<PaperTrade> {
    const response = await apiClient.post<PaperTrade>(`/backtesting/paper-trading/pause?paper_trade_id=${paperTradeId}`, {})
    return response.data
  },

  async getPaperTradingPositions(ticker: string): Promise<PaperTradePosition[]> {
    const response = await apiClient.get<PaperTradePosition[]>(`/backtesting/paper-trading/positions?ticker=${ticker}`)
    return response.data
  },

  async getPaperTradingHistory(limit?: number): Promise<PaperTrade[]> {
    const params = limit ? `?limit=${limit}` : ''
    const response = await apiClient.get<PaperTrade[]>(`/backtesting/paper-trading/history${params}`)
    return response.data
  },
}

