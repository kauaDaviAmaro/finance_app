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
} from 'chart.js'
import type { TechnicalAnalysis } from '../services/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps<{
  data: TechnicalAnalysis
}>()

const chartData = computed(() => {
  const labels = props.data.data.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const rsiValues = props.data.data.map((d) => d.rsi).filter((v) => v !== null && v !== undefined)

  return {
    labels: labels.filter((_, i) => props.data.data[i].rsi !== null && props.data.data[i].rsi !== undefined),
    datasets: [
      {
        label: 'RSI',
        data: rsiValues,
        borderColor: '#3b82f6',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: 'Sobrecomprado (70)',
        data: new Array(rsiValues.length).fill(70),
        borderColor: '#dc2626',
        borderDash: [5, 5],
        pointRadius: 0,
      },
      {
        label: 'Sobrevendido (30)',
        data: new Array(rsiValues.length).fill(30),
        borderColor: '#16a34a',
        borderDash: [5, 5],
        pointRadius: 0,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        font: {
          size: 11,
        },
        usePointStyle: true,
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
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
      min: 0,
      max: 100,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
    },
  },
}
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
