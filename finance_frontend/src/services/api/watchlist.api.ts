import { apiClient } from './apiClient'
import type { WatchlistResponse, WatchlistItem } from './types'

export const watchlistApi = {
  async getWatchlist(): Promise<WatchlistResponse> {
    const response = await apiClient.get<WatchlistResponse>('/watchlist')
    return response.data
  },

  async addToWatchlist(ticker: string): Promise<WatchlistItem> {
    const response = await apiClient.post<WatchlistItem>('/watchlist', { ticker })
    return response.data
  },

  async removeFromWatchlist(ticker: string): Promise<void> {
    await apiClient.delete(`/watchlist/${ticker}`)
  },
}

