import { apiClient } from './apiClient'
import type { 
  PortfolioSummary, 
  PortfolioItem, 
  PortfolioItemCreate, 
  PortfolioItemUpdate,
  Portfolio,
  PortfolioList,
  PortfolioCreate,
  PortfolioUpdate
} from './types'

export const portfolioApi = {
  // Portfolio CRUD
  async getPortfolios(): Promise<PortfolioList> {
    const response = await apiClient.get<PortfolioList>('/portfolio/portfolios')
    return response.data
  },

  async createPortfolio(data: PortfolioCreate): Promise<Portfolio> {
    const response = await apiClient.post<Portfolio>('/portfolio/portfolios', data)
    return response.data
  },

  async getPortfolioById(portfolioId: number): Promise<Portfolio> {
    const response = await apiClient.get<Portfolio>(`/portfolio/portfolios/${portfolioId}`)
    return response.data
  },

  async updatePortfolio(portfolioId: number, data: PortfolioUpdate): Promise<Portfolio> {
    const response = await apiClient.patch<Portfolio>(`/portfolio/portfolios/${portfolioId}`, data)
    return response.data
  },

  async deletePortfolio(portfolioId: number): Promise<void> {
    await apiClient.delete(`/portfolio/portfolios/${portfolioId}`)
  },

  // Portfolio Items
  async getPortfolio(portfolioId: number): Promise<PortfolioSummary> {
    const response = await apiClient.get<PortfolioSummary>(`/portfolio?portfolio_id=${portfolioId}`)
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

