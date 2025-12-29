import { useState, useEffect } from 'react'
import { getLeaderboard, getPlayer } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function LeaderboardView() {
  const [leaderboardData, setLeaderboardData] = useState<any>(null)
  const [player, setPlayer] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [scope, setScope] = useState<'team' | 'club'>('team')
  const [weekId, setWeekId] = useState<string>('')

  useEffect(() => {
    loadPlayer()
  }, [])

  useEffect(() => {
    if (!weekId) return
    
    loadLeaderboard()
  }, [weekId, scope])

  const loadPlayer = async () => {
    try {
      const data = await getPlayer()
      setPlayer(data.player)
      // Set current week as default
      if (data.currentWeek?.weekId) {
        setWeekId(data.currentWeek.weekId)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load player data')
    }
  }

  const loadLeaderboard = async () => {
    try {
      setLoading(true)
      const data = await getLeaderboard(weekId, scope)
      setLeaderboardData(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard')
    } finally {
      setLoading(false)
    }
  }

  if (!player) {
    return <Loading text="Loading..." />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Leaderboard</h1>
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
        {/* Scope Selector */}
        <div className="mb-6 flex items-center space-x-4">
          <span className="text-gray-700 font-medium">View:</span>
          <div className="flex space-x-2">
            <Button
              variant={scope === 'team' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setScope('team')}
            >
              Team
            </Button>
            <Button
              variant={scope === 'club' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setScope('club')}
            >
              Club
            </Button>
          </div>
        </div>

        {loading ? (
          <Loading text="Loading leaderboard..." />
        ) : error ? (
          <div className="text-center text-red-600">{error}</div>
        ) : leaderboardData ? (
          <>
            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Total Players</p>
                  <p className="text-2xl font-bold text-primary">
                    {leaderboardData.totalPlayers}
                  </p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Week</p>
                  <p className="text-2xl font-bold text-primary">
                    {leaderboardData.weekId}
                  </p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Scope</p>
                  <p className="text-2xl font-bold text-primary capitalize">
                    {leaderboardData.scope}
                  </p>
                </div>
              </Card>
            </div>

            {/* Podium (Top 3) */}
            {leaderboardData.leaderboard.length >= 3 && (
              <div className="mb-6 flex items-end justify-center space-x-4">
                {/* 2nd Place */}
                <div className="text-center">
                  <div className="bg-gray-300 rounded-t-lg p-4 mb-2" style={{ height: '120px' }}>
                    <div className="text-3xl font-bold">2</div>
                    <div className="text-sm mt-2">{`${leaderboardData.leaderboard[1].firstName || ''} ${leaderboardData.leaderboard[1].lastName || ''}`.trim() || 'Player'}</div>
                    <div className="text-lg font-semibold">{leaderboardData.leaderboard[1].weeklyScore}</div>
                  </div>
                </div>
                {/* 1st Place */}
                <div className="text-center">
                  <div className="bg-yellow-400 rounded-t-lg p-4 mb-2" style={{ height: '150px' }}>
                    <div className="text-3xl font-bold">1</div>
                    <div className="text-sm mt-2">{`${leaderboardData.leaderboard[0].firstName || ''} ${leaderboardData.leaderboard[0].lastName || ''}`.trim() || 'Player'}</div>
                    <div className="text-lg font-semibold">{leaderboardData.leaderboard[0].weeklyScore}</div>
                  </div>
                </div>
                {/* 3rd Place */}
                <div className="text-center">
                  <div className="bg-orange-300 rounded-t-lg p-4 mb-2" style={{ height: '100px' }}>
                    <div className="text-3xl font-bold">3</div>
                    <div className="text-sm mt-2">{`${leaderboardData.leaderboard[2].firstName || ''} ${leaderboardData.leaderboard[2].lastName || ''}`.trim() || 'Player'}</div>
                    <div className="text-lg font-semibold">{leaderboardData.leaderboard[2].weeklyScore}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Full Rankings */}
            <Card title="Full Rankings">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 text-gray-700">Rank</th>
                      <th className="text-left py-3 px-4 text-gray-700">Player</th>
                      <th className="text-right py-3 px-4 text-gray-700">Score</th>
                      <th className="text-right py-3 px-4 text-gray-700">Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboardData.leaderboard.map((entry: any) => (
                      <tr
                        key={entry.playerId}
                        className={`border-b ${
                          entry.isCurrentPlayer ? 'bg-primary bg-opacity-10' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-semibold">{entry.rank}</td>
                        <td className="py-3 px-4">
                          {`${entry.firstName || ''} ${entry.lastName || ''}`.trim() || 'Player'}
                          {entry.isCurrentPlayer && (
                            <span className="ml-2 text-xs text-primary">(You)</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right font-semibold">{entry.weeklyScore}</td>
                        <td className="py-3 px-4 text-right">{entry.daysCompleted}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  )
}

