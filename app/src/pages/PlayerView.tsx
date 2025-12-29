import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPlayer, getWeek, checkIn, Activity } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Button from '../components/ui/Button'
import ActivityFlyout from '../components/player/ActivityFlyout'

// Helper function to get week ID from date (YYYY-WW format)
function getWeekId(date: Date): string {
  const year = date.getFullYear()
  const startOfYear = new Date(year, 0, 1)
  const days = Math.floor((date.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000))
  const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7)
  return `${year}-${weekNumber.toString().padStart(2, '0')}`
}

// Helper function to get previous/next week ID
function getAdjacentWeekId(weekId: string, direction: 'prev' | 'next'): string {
  const [year, week] = weekId.split('-').map(Number)
  const date = new Date(year, 0, 1)
  const daysToAdd = (week - 1) * 7
  date.setDate(date.getDate() + daysToAdd)
  
  if (direction === 'prev') {
    date.setDate(date.getDate() - 7)
  } else {
    date.setDate(date.getDate() + 7)
  }
  
  return getWeekId(date)
}

export default function PlayerView() {
  const navigate = useNavigate()
  const [playerData, setPlayerData] = useState<any>(null)
  const [currentWeekId, setCurrentWeekId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [flyoutOpen, setFlyoutOpen] = useState(false)
  const [flyoutActivity, setFlyoutActivity] = useState<{ name: string; content: string } | null>(null)

  useEffect(() => {
    loadPlayerData()
  }, [])

  const loadPlayerData = async (weekId?: string) => {
    try {
      setLoading(true)
      const data = await getPlayer()
      const weekToLoad = weekId || data.currentWeek.weekId
      setCurrentWeekId(weekToLoad)
      
      // If loading a different week, fetch that week's data
      if (weekToLoad !== data.currentWeek.weekId) {
        const weekData = await getWeek(weekToLoad)
        setPlayerData({
          player: data.player,
          currentWeek: weekData
        })
      } else {
        setPlayerData(data)
      }
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load player data')
    } finally {
      setLoading(false)
    }
  }

  const handleWeekNavigation = (direction: 'prev' | 'next') => {
    if (!currentWeekId) return
    const newWeekId = getAdjacentWeekId(currentWeekId, direction)
    loadPlayerData(newWeekId)
  }

  const handleActivityClick = (activity: Activity) => {
    if (activity.activityType === 'flyout' && activity.flyoutContent) {
      setFlyoutActivity({
        name: activity.name,
        content: activity.flyoutContent
      })
      setFlyoutOpen(true)
    } else if (activity.activityType === 'link' && activity.contentSlug) {
      navigate(`/player/content-page/${activity.contentSlug}`)
    }
  }

  const handleCheckIn = async (activityId: string, date: string, completed: boolean) => {
    try {
      await checkIn(activityId, date, completed)
      // Reload data to reflect changes
      await loadPlayerData()
    } catch (err: any) {
      console.error('Failed to check in:', err)
      alert('Failed to update activity. Please try again.')
    }
  }

  if (loading) {
    return <Loading text="Loading your week..." />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => loadPlayerData()}>Retry</Button>
        </div>
      </div>
    )
  }

  if (!playerData) {
    return null
  }

  const { player, currentWeek } = playerData
  const activities = currentWeek.activities || []
  const dailyTracking = currentWeek.dailyTracking || {}
  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  
  // Get dates for current week (simplified - would need proper date calculation)
  const today = new Date()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{`${player.firstName || ''} ${player.lastName || ''}`.trim() || 'Player'}</h1>
            {player.clubId && (
              <p className="text-sm text-gray-600">Club: {player.clubId}</p>
            )}
            {player.teamId && (
              <p className="text-sm text-gray-600">Team: {player.teamId}</p>
            )}
          </div>
          <button
            onClick={() => setMenuOpen(true)}
            className="text-gray-600 hover:text-gray-800"
            aria-label="Open menu"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Navigation Menu */}
      <NavigationMenu player={player} isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Activity Flyout */}
      {flyoutActivity && (
        <ActivityFlyout
          isOpen={flyoutOpen}
          onClose={() => {
            setFlyoutOpen(false)
            setFlyoutActivity(null)
          }}
          activityName={flyoutActivity.name}
          content={flyoutActivity.content}
        />
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Weekly Score */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.preventDefault()
              handleWeekNavigation('prev')
            }}
            disabled={loading}
          >
            ← Previous
          </Button>
              <h2 className="text-xl font-semibold text-gray-800">Week {currentWeek.weekId}</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.preventDefault()
                  handleWeekNavigation('next')
                }}
                disabled={loading}
              >
                Next →
              </Button>
            </div>
            <div className="text-2xl font-bold text-primary">
              {currentWeek.weeklyScore} pts
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-primary h-4 rounded-full transition-all"
              style={{ width: `${Math.min((currentWeek.weeklyScore / (activities.length * 7 * 2)) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Activity Grid */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Activity</th>
                  {weekDays.map((day, idx) => {
                    const date = new Date(today)
                    date.setDate(today.getDate() - today.getDay() + 1 + idx)
                    return (
                      <th key={day} className="px-2 py-3 text-center text-xs font-semibold text-gray-700">
                        {day.substring(0, 3)}
                        <br />
                        <span className="text-gray-500">{date.getDate()}</span>
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {activities.map((activity: Activity) => (
                  <tr key={activity.activityId} className="border-t">
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        {(activity.activityType === 'flyout' && activity.flyoutContent) ||
                         (activity.activityType === 'link' && activity.contentSlug) ? (
                          <button
                            onClick={() => handleActivityClick(activity)}
                            className="font-medium text-gray-800 hover:text-primary cursor-pointer underline decoration-primary decoration-2 underline-offset-2"
                          >
                            {activity.name}
                          </button>
                        ) : (
                          <span className="font-medium text-gray-800">{activity.name}</span>
                        )}
                        {activity.scope && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            activity.scope === 'club' 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {activity.scope}
                          </span>
                        )}
                      </div>
                      {activity.description && (
                        <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                      )}
                    </td>
                    {weekDays.map((day, idx) => {
                      const date = new Date(today)
                      date.setDate(today.getDate() - today.getDay() + 1 + idx)
                      const dateStr = date.toISOString().split('T')[0]
                      const tracking = dailyTracking[dateStr]
                      const isCompleted = tracking?.completedActivities?.includes(activity.activityId) || false
                      
                      return (
                        <td key={`${activity.activityId}-${day}`} className="px-2 py-3 text-center">
                          <button
                            onClick={() => handleCheckIn(activity.activityId, dateStr, !isCompleted)}
                            className={`w-8 h-8 rounded transition-colors ${
                              isCompleted
                                ? 'bg-primary text-white'
                                : 'bg-gray-200 hover:bg-gray-300'
                            }`}
                            aria-label={`${isCompleted ? 'Unmark' : 'Mark'} ${activity.name} for ${day}`}
                          >
                            {isCompleted ? '✓' : ''}
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                ))}
                {/* Daily Score Row */}
                <tr className="border-t-2 border-gray-300 bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-800">Daily Score</td>
                  {weekDays.map((day, idx) => {
                    const date = new Date(today)
                    date.setDate(today.getDate() - today.getDay() + 1 + idx)
                    const dateStr = date.toISOString().split('T')[0]
                    const tracking = dailyTracking[dateStr]
                    const score = tracking?.dailyScore || 0
                    
                    return (
                      <td key={day} className="px-2 py-3 text-center font-semibold text-gray-800">
                        {score}
                      </td>
                    )
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}

