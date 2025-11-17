import { apiClient } from './apiClient'
import type { PortfolioRiskAnalysis, PositionRiskAnalysis } from './types'

export const riskApi = {
  /**
   * Obtém análise completa de risco de um portfólio
   */
  async getPortfolioRiskAnalysis(portfolioId: number): Promise<PortfolioRiskAnalysis> {
    const response = await apiClient.get<PortfolioRiskAnalysis>(`/risk/portfolio/${portfolioId}`)
    return response.data
  },

  /**
   * Obtém análise de risco de uma posição específica
   */
  async getPositionRiskAnalysis(itemId: number): Promise<PositionRiskAnalysis> {
    const response = await apiClient.get<PositionRiskAnalysis>(`/risk/position/${itemId}`)
    return response.data
  },
}

