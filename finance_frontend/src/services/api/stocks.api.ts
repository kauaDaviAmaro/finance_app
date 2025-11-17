import { apiClient } from './apiClient'
import type { 
  TickerHistoricalData, TechnicalAnalysis, Fundamentals, MostSearchedTicker, 
  TickerComparisonRequest, TickerComparison, FinancialStatements,
  AdvancedAnalysis, ElliottAnnotation, ElliottAnnotationCreate
} from './types'

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

  async getMostSearchedTickers(limit: number = 10, days: number = 7): Promise<MostSearchedTicker[]> {
    const response = await apiClient.get<MostSearchedTicker[]>('/stocks/most-searched', {
      params: { limit, days },
    })
    return response.data
  },

  async compareTickers(ticker1: string, ticker2: string, period: string = '1y'): Promise<TickerComparison> {
    const response = await apiClient.post<TickerComparison>('/stocks/compare', {
      ticker1,
      ticker2,
      period,
    })
    return response.data
  },

  async getFinancialStatements(ticker: string): Promise<FinancialStatements> {
    const response = await apiClient.get<FinancialStatements>(`/stocks/financial-statements/${ticker}`)
    return response.data
  },

  // Advanced Analysis (PRO only)
  async getAdvancedAnalysis(ticker: string, period: string = '1y'): Promise<AdvancedAnalysis> {
    const response = await apiClient.post<AdvancedAnalysis>('/stocks/advanced-analysis', {
      ticker,
      period,
    })
    return response.data
  },

  async saveElliottAnnotations(payload: ElliottAnnotationCreate): Promise<ElliottAnnotation> {
    const response = await apiClient.post<ElliottAnnotation>('/stocks/elliott-annotations', payload)
    return response.data
  },

  async getElliottAnnotations(ticker: string, period: string = '1y'): Promise<ElliottAnnotation | null> {
    const response = await apiClient.get<ElliottAnnotation | null>(`/stocks/elliott-annotations/${ticker}`, {
      params: { period },
    })
    return response.data
  },

  async deleteElliottAnnotations(ticker: string, period: string = '1y'): Promise<void> {
    await apiClient.delete(`/stocks/elliott-annotations/${ticker}`, {
      params: { period },
    })
  },
}

