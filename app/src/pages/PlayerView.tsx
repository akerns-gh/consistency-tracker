import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getPlayer, checkIn, Activity, DailyTracking } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Button from '../components/ui/Button'

export default function PlayerView() {
  const { uniqueLink } = useParams<{ uniqueLink: string }>()
  const [playerData, setPlayerData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (!uniqueLink) return
    
    loadPlayerData()
  }, [uniqueLink])

  const loadPlayerData = async () => {
    try {
      setLoading(true)
      const data = await getPlayer(uniqueLink!)
      setPlayerData(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load player data')
    } finally {
      setLoading(false)
    }
  }

  const handleCheckIn = async (activityId: string, date: string, completed: boolean) => {
    if (!uniqueLink) return
    
    try {
      await checkIn(uniqueLink, activityId, date, completed)
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
          <Button onClick={loadPlayerData}>Retry</Button>
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
  const currentDate = today.toISOString().split('T')[0]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{player.name}</h1>
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Weekly Score */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Week {currentWeek.weekId}</h2>
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
                    const dateStr = date.toISOString().split('T')[0]
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
                        <span className="font-medium text-gray-800">{activity.name}</span>
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
                        <td key={day} className="px-2 py-3 text-center">
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

