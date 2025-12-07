import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getProgress } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'

export default function MyProgressView() {
  const { uniqueLink } = useParams<{ uniqueLink: string }>()
  const [progressData, setProgressData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (!uniqueLink) return
    
    loadProgress()
  }, [uniqueLink])

  const loadProgress = async () => {
    try {
      setLoading(true)
      const data = await getProgress(uniqueLink!)
      setProgressData(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load progress data')
    } finally {
      setLoading(false)
    }
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
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Current Week</p>
              <p className="text-3xl font-bold text-primary">
                {weeks[0]?.weeklyScore || 0}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Average Score</p>
              <p className="text-3xl font-bold text-primary">
                {statistics.averageScore.toFixed(1)}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Best Week</p>
              <p className="text-3xl font-bold text-primary">
                {statistics.bestWeek?.weeklyScore || 0}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Total Weeks</p>
              <p className="text-3xl font-bold text-primary">
                {statistics.totalWeeks}
              </p>
            </div>
          </Card>
        </div>

        {/* Weekly Breakdown */}
        <Card title="Weekly Breakdown">
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
                  <tr key={week.weekId} className="border-b">
                    <td className="py-3 px-4">{week.weekId}</td>
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

