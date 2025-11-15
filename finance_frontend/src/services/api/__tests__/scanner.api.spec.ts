import { vi, describe, it, expect } from 'vitest'
import { apiClient } from '../../api/apiClient'
import { getScannerResults } from '../../api/scanner.api'

vi.mock('../../api/apiClient', () => {
  return {
    apiClient: {
      get: vi.fn(),
    },
  }
})

describe('scanner.api', () => {
  it('maps params to querystring correctly', async () => {
    ;(apiClient.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: [] })

    await getScannerResults({ rsi_lt: 30, macd_gt: 0, bb_touch: 'upper', sort: 'rsi_asc', limit: 50 })

    expect(apiClient.get).toHaveBeenCalledWith('/stocks/scanner', {
      params: { rsi_lt: 30, macd_gt: 0, bb_touch: 'upper', sort: 'rsi_asc', limit: 50 },
    })
  })
})







