<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Scanner (PRO)</h1>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
      <div>
        <label class="block text-sm font-medium mb-1">RSI</label>
        <div class="flex gap-2">
          <select v-model="rsiOp" class="border rounded px-2 py-1 w-20">
            <option value="lt">&lt;</option>
            <option value="gt">&gt;</option>
          </select>
          <input type="number" v-model.number="rsiVal" class="border rounded px-2 py-1 flex-1" placeholder="30" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">MACD Hist.</label>
        <div class="flex gap-2">
          <select v-model="macdOp" class="border rounded px-2 py-1 w-20">
            <option value="gt">&gt;</option>
            <option value="lt">&lt;</option>
          </select>
          <input type="number" v-model.number="macdVal" step="0.01" class="border rounded px-2 py-1 flex-1" placeholder="0" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Bandas</label>
        <select v-model="bbTouch" class="border rounded px-2 py-1 w-full">
          <option :value="undefined">—</option>
          <option value="upper">Toque superior</option>
          <option value="lower">Toque inferior</option>
          <option value="any">Qualquer toque</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Ordenar</label>
        <select v-model="sort" class="border rounded px-2 py-1 w-full">
          <option :value="undefined">—</option>
          <option value="rsi_asc">RSI ↑</option>
          <option value="rsi_desc">RSI ↓</option>
          <option value="macd_desc">MACD Hist. ↓</option>
        </select>
      </div>
    </div>

    <div class="flex items-center gap-3 mb-4">
      <button @click="fetchResults" class="bg-blue-600 text-white px-4 py-2 rounded" :disabled="loading">
        {{ loading ? 'Carregando...' : 'Filtrar' }}
      </button>
      <span v-if="error" class="text-red-600">{{ error }}</span>
    </div>

    <div v-if="results.length === 0 && !loading" class="text-gray-500">Nenhum resultado.</div>

    <div v-if="results.length">
      <table class="min-w-full border">
        <thead>
          <tr class="bg-gray-100">
            <th class="p-2 border">Ticker</th>
            <th class="p-2 border">Preço</th>
            <th class="p-2 border">RSI(14)</th>
            <th class="p-2 border">MACD Hist.</th>
            <th class="p-2 border">BB Lower</th>
            <th class="p-2 border">BB Upper</th>
            <th class="p-2 border">Atualização</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in results" :key="row.ticker">
            <td class="p-2 border">{{ row.ticker }}</td>
            <td class="p-2 border">{{ formatNum(row.last_price) }}</td>
            <td class="p-2 border">{{ formatNum(row.rsi_14) }}</td>
            <td class="p-2 border">{{ formatNum(row.macd_h) }}</td>
            <td class="p-2 border">{{ formatNum(row.bb_lower) }}</td>
            <td class="p-2 border">{{ formatNum(row.bb_upper) }}</td>
            <td class="p-2 border">{{ formatDate(row.timestamp) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getScannerResults } from '../services/api/scanner.api'
import type { ScannerRow, ScannerSort } from '../services/api/types'

const results = ref<ScannerRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const rsiOp = ref<'lt' | 'gt'>('lt')
const rsiVal = ref<number | undefined>(30)
const macdOp = ref<'lt' | 'gt'>('gt')
const macdVal = ref<number | undefined>(0)
const bbTouch = ref<'upper' | 'lower' | 'any' | undefined>(undefined)
const sort = ref<ScannerSort | undefined>('rsi_asc')

function buildParams() {
  const params: Record<string, unknown> = {}
  if (rsiVal.value !== undefined && rsiVal.value !== null) {
    params[rsiOp.value === 'lt' ? 'rsi_lt' : 'rsi_gt'] = rsiVal.value
  }
  if (macdVal.value !== undefined && macdVal.value !== null) {
    params[macdOp.value === 'gt' ? 'macd_gt' : 'macd_lt'] = macdVal.value
  }
  if (bbTouch.value) params['bb_touch'] = bbTouch.value
  if (sort.value) params['sort'] = sort.value
  return params
}

async function fetchResults() {
  loading.value = true
  error.value = null
  try {
    const data = await getScannerResults(buildParams())
    results.value = data
  } catch (e: any) {
    error.value = e?.message || 'Erro ao carregar resultados'
  } finally {
    loading.value = false
  }
}

function formatNum(n: number | null | undefined) {
  if (n === null || n === undefined) return '-'
  return Number(n).toFixed(2)
}

function formatDate(s: string | undefined) {
  if (!s) return '-'
  try {
    const d = new Date(s)
    return d.toLocaleString()
  } catch {
    return s
  }
}

// Carrega com filtros padrão
fetchResults()
</script>

<style scoped>
</style>




