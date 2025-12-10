import { useState, useEffect } from 'react'
import { getOverview } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Loading from '../../ui/Loading'

interface SummaryData {
  totalPlayers: number
  averageScore: number
  totalWeeks: number
  contentPages: number
}

export default function SummaryCards() {
  const [data, setData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const response = await getOverview()
      setData({
        totalPlayers: response.totalPlayers || 0,
        averageScore: response.averageScore || 0,
        totalWeeks: response.totalWeeks || 0,
        contentPages: response.contentPages || 0,
      })
    } catch (err) {
      console.error('Failed to load overview data:', err)
      setData({
        totalPlayers: 0,
        averageScore: 0,
        totalWeeks: 0,
        contentPages: 0,
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Loading text="Loading overview..." />
  }

  if (!data) {
    return null
  }

  const cards = [
    { label: 'Total Players', value: data.totalPlayers, icon: '👥' },
    { label: 'Average Score', value: data.averageScore.toFixed(1), icon: '📊' },
    { label: 'Total Weeks', value: data.totalWeeks, icon: '📅' },
    { label: 'Content Pages', value: data.contentPages, icon: '📄' },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <div className="text-center">
            <div className="text-3xl mb-2">{card.icon}</div>
            <p className="text-sm text-gray-600 mb-1">{card.label}</p>
            <p className="text-2xl font-bold" style={{ color: 'rgb(150, 200, 85)' }}>
              {card.value}
            </p>
          </div>
        </Card>
      ))}
    </div>
  )
}

