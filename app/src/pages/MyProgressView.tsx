import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getProgress, getPlayer, getWeek } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import ProgressChart from '../components/progress/ProgressChart'
import SummaryCardsCarousel from '../components/progress/SummaryCardsCarousel'

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

export default function MyProgressView() {
  const { uniqueLink } = useParams<{ uniqueLink: string }>()
  const [progressData, setProgressData] = useState<any>(null)
  const [currentWeekId, setCurrentWeekId] = useState<string | null>(null)
  const [activityStats, setActivityStats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (!uniqueLink) return
    
    loadProgress()
  }, [uniqueLink])

  const loadProgress = async (weekId?: string) => {
    try {
      setLoading(true)
      const data = await getProgress(uniqueLink!)
      setProgressData(data)
      
      // Load activity stats for current week
      const weekToLoad = weekId || data.weeks[0]?.weekId
      if (weekToLoad) {
        setCurrentWeekId(weekToLoad)
        await loadActivityStats(weekToLoad)
      }
      
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load progress data')
    } finally {
      setLoading(false)
    }
  }

  const loadActivityStats = async (weekId: string) => {
    try {
      const weekData = await getWeek(uniqueLink!, weekId)
      const activities = weekData.activities || []
      const dailyTracking = weekData.dailyTracking || {}
      
      // Calculate activity completion stats
      const stats = activities.map((activity: any) => {
        let completedCount = 0
        const totalDays = 7
        
        Object.values(dailyTracking).forEach((tracking: any) => {
          if (tracking.completedActivities?.includes(activity.activityId)) {
            completedCount++
          }
        })
        
        return {
          activityId: activity.activityId,
          name: activity.name,
          completed: completedCount,
          total: totalDays,
          percentage: Math.round((completedCount / totalDays) * 100),
        }
      })
      
      setActivityStats(stats)
    } catch (err) {
      console.error('Failed to load activity stats:', err)
    }
  }

  const handleWeekNavigation = async (direction: 'prev' | 'next') => {
    if (!currentWeekId || !progressData) return
    
    const newWeekId = getAdjacentWeekId(currentWeekId, direction)
    setCurrentWeekId(newWeekId)
    await loadActivityStats(newWeekId)
  }

  if (loading) {
    return <Loading text="Loading your progress..." />
  }

  if (error || !progressData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">{error || 'No data available'}</p>
        </div>
      </div>
    )
  }

  const { player, weeks, statistics } = progressData

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">My Progress</h1>
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

      <NavigationMenu player={player} isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Summary Cards Carousel */}
        <SummaryCardsCarousel
          cards={[
            {
              label: 'Current Week',
              value: weeks[0]?.weeklyScore || 0,
              subtitle: `Week ${weeks[0]?.weekId || 'N/A'}`,
            },
            {
              label: 'Average Score',
              value: statistics.averageScore.toFixed(1),
              subtitle: 'Across all weeks',
            },
            {
              label: 'Best Week',
              value: statistics.bestWeek?.weeklyScore || 0,
              subtitle: statistics.bestWeek ? `Week ${statistics.bestWeek.weekId}` : 'N/A',
            },
            {
              label: 'Total Weeks',
              value: statistics.totalWeeks,
              subtitle: 'Weeks tracked',
            },
            {
              label: 'Total Score',
              value: statistics.totalScore || 0,
              subtitle: 'All-time points',
            },
          ]}
        />

        {/* Weekly Scores Chart */}
        {weeks.length > 0 && (
          <Card title="Weekly Scores Over Time" className="mb-6">
            <ProgressChart weeks={weeks} />
          </Card>
        )}

        {/* Activity Progress Indicators */}
        {activityStats.length > 0 && currentWeekId && (
          <Card title={`Activity Progress - Week ${currentWeekId}`} className="mb-6">
            <div className="space-y-4">
              {activityStats.map((stat) => (
                <div key={stat.activityId}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">{stat.name}</span>
                    <span className="text-sm text-gray-600">
                      {stat.completed}/{stat.total} days ({stat.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${stat.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Weekly Breakdown */}
        <Card title="Weekly Breakdown">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleWeekNavigation('prev')}
                disabled={loading || !currentWeekId}
              >
                ← Previous
              </Button>
              {currentWeekId && (
                <span className="text-sm text-gray-600">Viewing: Week {currentWeekId}</span>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleWeekNavigation('next')}
                disabled={loading || !currentWeekId}
              >
                Next →
              </Button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-gray-700">Week</th>
                  <th className="text-right py-3 px-4 text-gray-700">Score</th>
                  <th className="text-right py-3 px-4 text-gray-700">Days Completed</th>
                  <th className="text-right py-3 px-4 text-gray-700">Perfect Days</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((week: any) => (
                  <tr
                    key={week.weekId}
                    className={`border-b ${
                      week.weekId === currentWeekId ? 'bg-primary bg-opacity-10' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      {week.weekId}
                      {week.weekId === currentWeekId && (
                        <span className="ml-2 text-xs text-primary">(Current)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">{week.weeklyScore}</td>
                    <td className="py-3 px-4 text-right">{week.daysCompleted}</td>
                    <td className="py-3 px-4 text-right">{week.perfectDays}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </main>
    </div>
  )
}

