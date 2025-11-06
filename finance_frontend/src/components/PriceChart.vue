<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { TechnicalAnalysis } from '../services/api/index'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Props {
  data: TechnicalAnalysis
}

const props = defineProps<Props>()

const chartData = computed(() => {
  if (!props.data || !props.data.data || props.data.data.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = props.data.data.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const closePrices = props.data.data.map((d) => d.close)

  return {
    labels,
    datasets: [
      {
        label: 'Preço de Fechamento',
        data: closePrices,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
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
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      callbacks: {
        label: function (context: any) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
          }).format(context.parsed.y)
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
}
</script>

<template>
  <div v-if="chartData.labels.length > 0" class="chart-container">
    <Line :data="chartData" :options="chartOptions" />
  </div>
  <div v-else class="chart-container empty">
    <p>Nenhum dado disponível para exibir</p>
  </div>
</template>

<style scoped>
.chart-container {
  height: 400px;
  position: relative;
}

.chart-container.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
}
</style>
