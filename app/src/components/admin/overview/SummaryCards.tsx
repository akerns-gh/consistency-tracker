import { useState, useEffect } from 'react'
import { useAuth } from '../../../contexts/AuthContext'
import { useViewAsClubAdmin } from '../../../contexts/ViewAsClubAdminContext'
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
  const { isAppAdmin } = useAuth()
  const { isViewingAsClubAdmin, selectedClubId } = useViewAsClubAdmin()
  const [data, setData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [isAppAdmin, isViewingAsClubAdmin, selectedClubId])

  const loadData = async () => {
    // For app_admins not viewing as club admin, skip loading overview data
    if (isAppAdmin && !isViewingAsClubAdmin) {
      setData(null)
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      // Pass clubId if viewing as club admin
      const clubId = isViewingAsClubAdmin ? selectedClubId : undefined
      const response = await getOverview(clubId)
      // Map from backend response structure
      const currentWeek = response.currentWeek || {}
      setData({
        totalPlayers: currentWeek.totalPlayers || 0,
        averageScore: currentWeek.averageWeeklyScore || 0,
        totalWeeks: 0, // Not provided by backend
        contentPages: response.activities?.total || 0,
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

  // For app_admins not viewing as club admin, show message instead of stats
  if (isAppAdmin && !isViewingAsClubAdmin) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-600 mb-2">
            Overview statistics are available when viewing as a club admin.
          </p>
          <p className="text-sm text-gray-500">
            Use the "View As" button in Club Management to see club-specific statistics.
          </p>
        </div>
      </Card>
    )
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

