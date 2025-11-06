import { apiClient } from './apiClient'
import type { PortfolioSummary, PortfolioItem, PortfolioItemCreate, PortfolioItemUpdate } from './types'

export const portfolioApi = {
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
}

