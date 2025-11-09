<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  BarController,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import type { TechnicalAnalysis } from '../services/api/index'
import type { ChartData, ChartOptions } from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  BarController,
  Title,
  Tooltip,
  Legend
)

ChartJS.defaults.set('bar', {
  datasets: {
    bar: {
      barPercentage: 0.6,
      categoryPercentage: 0.8,
    },
  },
})

const props = defineProps<{
  data: TechnicalAnalysis
}>()

const chartData = computed((): ChartData<'line'> => {
  const validData = props.data.data.filter((d) => d.macd !== null && d.macd !== undefined)
  const labels = validData.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const macd = validData.map((d) => d.macd!)
  const macdSignal = validData.map((d) => d.macd_signal || null)
  const macdHistogram = validData.map((d) => d.macd_histogram || null)

  return {
    labels,
    datasets: [
      {
        label: 'MACD',
        data: macd,
        borderColor: '#3b82f6',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
        order: 2,
        type: 'line',
      },
      {
        label: 'Sinal',
        data: macdSignal,
        borderColor: '#f59e0b',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
        order: 2,
        type: 'line',
      },
      {
        label: 'Histograma',
        data: macdHistogram,
        backgroundColor: macdHistogram.map((v) => {
          if (v === null || v === undefined) return 'transparent'
          return v >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
        }) as string[],
        borderColor: macdHistogram.map((v) => {
          if (v === null || v === undefined) return 'transparent'
          return v >= 0 ? '#10b981' : '#ef4444'
        }) as string[],
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y1',
        order: 1,
      } as any,
    ],
  }
})

const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        font: {
          size: 11,
        },
        usePointStyle: true,
        padding: 12,
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 13,
        weight: 'bold',
      },
      bodyFont: {
        size: 12,
      },
      callbacks: {
        label: function (context: any) {
          let label = context.dataset.label || ''
          if (label) {
            label += ': '
          }
          if (context.parsed.y !== null) {
            label += context.parsed.y.toFixed(4)
          }
          return label
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        maxTicksLimit: 10,
        font: {
          size: 11,
        },
      },
    },
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      grid: {
        drawOnChartArea: false,
      },
      ticks: {
        font: {
          size: 11,
        },
      },
    },
  },
} as any
</script>

<template>
  <div class="chart-container">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-container {
  height: 300px;
  position: relative;
}
</style>