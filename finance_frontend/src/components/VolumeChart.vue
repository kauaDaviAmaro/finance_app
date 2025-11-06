<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import type { TechnicalAnalysis } from '../services/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps<{
  data: TechnicalAnalysis
}>()

const chartData = computed(() => {
  const labels = props.data.data.map((d) => new Date(d.date).toLocaleDateString('pt-BR'))
  const volumes = props.data.data.map((d) => d.volume)

  return {
    labels,
    datasets: [
      {
        label: 'Volume',
        data: volumes,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: '#3b82f6',
        borderWidth: 1,
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
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        callback: function (value: any) {
          if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M'
          }
          if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K'
          }
          return value
        },
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
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-container {
  height: 250px;
  position: relative;
}
</style>
