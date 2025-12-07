import React from 'react'
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
import { Line } from 'react-chartjs-2'

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

interface ProgressChartProps {
  weeks: Array<{
    weekId: string
    weeklyScore: number
  }>
}

export default function ProgressChart({ weeks }: ProgressChartProps) {
  // Reverse to show oldest to newest
  const reversedWeeks = [...weeks].reverse()
  
  const labels = reversedWeeks.map((week) => `Week ${week.weekId.split('-')[1]}`)
  const scores = reversedWeeks.map((week) => week.weeklyScore)

  const data = {
    labels,
    datasets: [
      {
        label: 'Weekly Score',
        data: scores,
        borderColor: 'rgb(150, 200, 85)',
        backgroundColor: 'rgba(150, 200, 85, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgb(150, 200, 85)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: 'bold' as const,
        },
        bodyFont: {
          size: 13,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 5,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  }

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  )
}

