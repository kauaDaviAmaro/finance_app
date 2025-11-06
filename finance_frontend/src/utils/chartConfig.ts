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

// Registrar todos os componentes do Chart.js
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

// Configuração global padrão para todos os gráficos
ChartJS.defaults.responsive = true
ChartJS.defaults.maintainAspectRatio = false
ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.85)'
ChartJS.defaults.plugins.tooltip.padding = 12
ChartJS.defaults.plugins.tooltip.titleColor = '#ffffff'
ChartJS.defaults.plugins.tooltip.bodyColor = '#ffffff'
ChartJS.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)'
ChartJS.defaults.plugins.tooltip.borderWidth = 1
ChartJS.defaults.plugins.legend.labels.usePointStyle = true
ChartJS.defaults.plugins.legend.labels.padding = 12

// Configuração de animação
ChartJS.defaults.animation = {
  duration: 1000,
  easing: 'easeInOutQuart' as const,
}

// Configuração de elementos
ChartJS.defaults.elements.line.tension = 0.4
ChartJS.defaults.elements.point.radius = 0
ChartJS.defaults.elements.point.hoverRadius = 4

export default ChartJS
