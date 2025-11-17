import { apiClient } from './apiClient'
import type { ScannerRow, ScannerSort } from './types'

export interface ScannerParams {
  rsi_lt?: number
  rsi_gt?: number
  macd_gt?: number
  macd_lt?: number
  bb_touch?: 'upper' | 'lower' | 'any'
  sort?: ScannerSort
  limit?: number
}

export async function getScannerResults(params: ScannerParams = {}): Promise<ScannerRow[]> {
  const { data } = await apiClient.get<ScannerRow[]>('/stocks/scanner', { params })
  return data
}









