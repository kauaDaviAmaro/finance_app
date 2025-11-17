<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { Line, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { 
  TechnicalAnalysis, AdvancedAnalysis, SupportResistanceLevel, 
  ChartPattern, CandlestickPattern, ElliottWaves, ElliottWavePoint, WavePoint
} from '../services/api/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Props {
  technicalData: TechnicalAnalysis
  advancedAnalysis: AdvancedAnalysis | null
  manualElliottWaves?: WavePoint[]
  showSupportResistance?: boolean
  showFibonacci?: boolean
  showPatterns?: boolean
  showElliottWaves?: boolean
  showCandlestickPatterns?: boolean
  editMode?: boolean
  onChartClick?: (event: any) => void
}

const props = withDefaults(defineProps<Props>(), {
  showSupportResistance: true,
  showFibonacci: true,
  showPatterns: true,
  showElliottWaves: true,
  showCandlestickPatterns: true,
  editMode: false,
})

const chartRef = ref<any>(null)

const chartData = computed(() => {
  if (!props.technicalData || !props.technicalData.data || props.technicalData.data.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = props.technicalData.data.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const closes = props.technicalData.data.map((d) => d.close)
  const highs = props.technicalData.data.map((d) => d.high)
  const lows = props.technicalData.data.map((d) => d.low)
  const opens = props.technicalData.data.map((d) => d.open)

  const datasets: any[] = [
    {
      label: 'Preço de Fechamento',
      data: closes,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 4,
      order: 1,
    },
  ]

  // Adicionar níveis de suporte
  if (props.showSupportResistance && props.advancedAnalysis) {
    props.advancedAnalysis.support_levels.forEach((level, idx) => {
      datasets.push({
        label: `Suporte ${idx + 1}`,
        data: new Array(closes.length).fill(level.price),
        borderColor: '#10b981',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        pointHoverRadius: 0,
        order: 2,
      })
    })
  }

  // Adicionar níveis de resistência
  if (props.showSupportResistance && props.advancedAnalysis) {
    props.advancedAnalysis.resistance_levels.forEach((level, idx) => {
      datasets.push({
        label: `Resistência ${idx + 1}`,
        data: new Array(closes.length).fill(level.price),
        borderColor: '#ef4444',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        pointHoverRadius: 0,
        order: 2,
      })
    })
  }

  // Adicionar níveis de Fibonacci
  if (props.showFibonacci && props.advancedAnalysis && props.advancedAnalysis.fibonacci_levels) {
    const fibLevels = props.advancedAnalysis.fibonacci_levels
    const fibKeys = ['23.6', '38.2', '50.0', '61.8', '78.6']
    
    fibKeys.forEach((key) => {
      const level = fibLevels[`level_${key.replace('.', '')}`]
      if (level !== undefined) {
        datasets.push({
          label: `Fib ${key}%`,
          data: new Array(closes.length).fill(level),
          borderColor: '#8b5cf6',
          borderWidth: 1,
          borderDash: [2, 2],
          pointRadius: 0,
          pointHoverRadius: 0,
          order: 3,
        })
      }
    })
  }

  return {
    labels,
    datasets,
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        filter: (item: any) => {
          // Mostrar apenas legenda para preço, suporte/resistência principais e Fibonacci
          return item.text === 'Preço de Fechamento' || 
                 item.text.includes('Suporte 1') || 
                 item.text.includes('Resistência 1') ||
                 item.text.includes('Fib')
        },
        font: {
          size: 11,
        },
      },
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      padding: 12,
      titleFont: {
        size: 14,
        weight: 'bold' as const,
      },
      bodyFont: {
        size: 13,
      },
      callbacks: {
        label: function (context: any) {
          return `${context.dataset.label}: ${new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(context.parsed.y)}`
        },
      },
    },
    annotation: {
      annotations: getAnnotations(),
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        maxTicksLimit: 15,
        font: {
          size: 11,
        },
      },
    },
    y: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        callback: function (value: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(value)
        },
        font: {
          size: 11,
        },
      },
    },
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false,
  },
  onClick: props.editMode && props.onChartClick ? props.onChartClick : undefined,
}))

function getAnnotations() {
  const annotations: any = {}
  
  if (!props.advancedAnalysis) return annotations

  // Anotações para padrões gráficos
  if (props.showPatterns) {
    props.advancedAnalysis.patterns.forEach((pattern, idx) => {
      annotations[`pattern_${idx}`] = {
        type: 'box',
        xMin: pattern.start_date,
        xMax: pattern.end_date,
        backgroundColor: pattern.trend === 'BULLISH' ? 'rgba(16, 185, 129, 0.1)' : 
                        pattern.trend === 'BEARISH' ? 'rgba(239, 68, 68, 0.1)' : 
                        'rgba(139, 92, 246, 0.1)',
        borderColor: pattern.trend === 'BULLISH' ? 'rgba(16, 185, 129, 0.5)' : 
                     pattern.trend === 'BEARISH' ? 'rgba(239, 68, 68, 0.5)' : 
                     'rgba(139, 92, 246, 0.5)',
        borderWidth: 1,
        label: {
          display: true,
          content: pattern.pattern_name,
          position: 'start' as const,
          font: {
            size: 10,
          },
        },
      }
    })
  }

  return annotations
}

// Função para encontrar índice de data no gráfico
function findDateIndex(date: string): number {
  if (!props.technicalData?.data) return -1
  const targetDateStr = new Date(date).toISOString().split('T')[0]
  return props.technicalData.data.findIndex(
    (d) => {
      const dataDateStr = new Date(d.date).toISOString().split('T')[0]
      return dataDateStr === targetDateStr
    }
  )
}
</script>

<template>
  <div class="advanced-chart-container">
    <div v-if="chartData.labels.length > 0" class="chart-wrapper">
      <Line :data="chartData" :options="chartOptions" ref="chartRef" />
      
      <!-- Overlay para anotações de padrões e ondas de Elliott -->
      <div v-if="advancedAnalysis" class="chart-annotations">
        <!-- Padrões de candlestick -->
        <template v-if="showCandlestickPatterns">
          <div
            v-for="(pattern, idx) in advancedAnalysis.candlestick_patterns"
            :key="`candle_${idx}`"
            class="candlestick-pattern-marker"
            :style="{
              left: `${(findDateIndex(pattern.date) / chartData.labels.length) * 100}%`,
              top: '10px',
              backgroundColor: pattern.signal === 'BULLISH' ? '#10b981' : 
                              pattern.signal === 'BEARISH' ? '#ef4444' : '#64748b',
            }"
            :title="pattern.pattern_name"
          >
            <span class="pattern-icon">{{ pattern.signal === 'BULLISH' ? '↑' : pattern.signal === 'BEARISH' ? '↓' : '○' }}</span>
          </div>
        </template>

        <!-- Ondas de Elliott automáticas -->
        <template v-if="showElliottWaves && advancedAnalysis.elliott_waves.waves.length > 0">
          <div
            v-for="(wave, idx) in advancedAnalysis.elliott_waves.waves"
            :key="`wave_auto_${idx}`"
            class="elliott-wave-marker auto"
            :style="{
              left: `${(findDateIndex(wave.date) / chartData.labels.length) * 100}%`,
              bottom: `${((wave.price - Math.min(...chartData.datasets[0].data)) / 
                        (Math.max(...chartData.datasets[0].data) - Math.min(...chartData.datasets[0].data))) * 100}%`,
            }"
            :title="`Onda ${wave.wave}`"
          >
            <span class="wave-label">{{ wave.wave }}</span>
          </div>
        </template>

        <!-- Ondas de Elliott manuais -->
        <template v-if="showElliottWaves && manualElliottWaves && manualElliottWaves.length > 0">
          <div
            v-for="(wave, idx) in manualElliottWaves"
            :key="`wave_manual_${idx}`"
            class="elliott-wave-marker manual"
            :style="{
              left: `${(findDateIndex(wave.date) / chartData.labels.length) * 100}%`,
              bottom: `${((wave.price - Math.min(...chartData.datasets[0].data)) / 
                        (Math.max(...chartData.datasets[0].data) - Math.min(...chartData.datasets[0].data))) * 100}%`,
            }"
            :title="`Onda ${wave.wave} (Manual)`"
          >
            <span class="wave-label">{{ wave.wave }}</span>
          </div>
        </template>
      </div>
    </div>
    <div v-else class="chart-container empty">
      <p>Nenhum dado disponível para exibir</p>
    </div>
  </div>
</template>

<style scoped>
.advanced-chart-container {
  position: relative;
  height: 500px;
  width: 100%;
}

.chart-wrapper {
  position: relative;
  height: 100%;
  width: 100%;
}

.chart-annotations {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.candlestick-pattern-marker {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  cursor: pointer;
  transform: translate(-50%, -50%);
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.pattern-icon {
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.elliott-wave-marker {
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  cursor: pointer;
  transform: translate(-50%, 50%);
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.elliott-wave-marker.auto {
  background-color: #3b82f6;
}

.elliott-wave-marker.manual {
  background-color: #f59e0b;
}

.wave-label {
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.chart-container.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
  height: 100%;
}
</style>

