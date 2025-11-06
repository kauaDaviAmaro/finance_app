import { apiClient } from './apiClient'
import type { TickerHistoricalData, TechnicalAnalysis, Fundamentals } from './types'

export const stocksApi = {
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
}

