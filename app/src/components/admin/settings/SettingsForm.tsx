import { useState, useEffect } from 'react'
import { getTeams, Team, advanceWeek } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Loading from '../../ui/Loading'

export default function SettingsForm() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTeam, setSelectedTeam] = useState<string>('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const teamsData = await getTeams()
      setTeams(teamsData.teams || [])
      if (teamsData.teams && teamsData.teams.length > 0) {
        setSelectedTeam(teamsData.teams[0].teamId)
      }
    } catch (err) {
      console.error('Failed to load settings data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdvanceWeek = async () => {
    if (!confirm('Are you sure you want to advance to the next week? This action cannot be undone.')) {
      return
    }
    try {
      const result = await advanceWeek()
      alert(`Week advanced successfully to ${result.newWeekId}`)
    } catch (err: any) {
      alert(err.message || 'Failed to advance week')
    }
  }

  if (loading) {
    return <Loading text="Loading settings..." />
  }

  return (
    <div className="space-y-6">
      <Card title="Team Information">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Team
            </label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              {teams.map((team) => (
                <option key={team.teamId} value={team.teamId}>
                  {team.teamName}
                </option>
              ))}
            </select>
          </div>
          {selectedTeam && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              {teams.find((t) => t.teamId === selectedTeam) && (
                <>
                  <p className="text-sm text-gray-600">
                    <strong>Team Name:</strong> {teams.find((t) => t.teamId === selectedTeam)?.teamName}
                  </p>
                  {teams.find((t) => t.teamId === selectedTeam)?.coachName && (
                    <p className="text-sm text-gray-600 mt-1">
                      <strong>Coach:</strong> {teams.find((t) => t.teamId === selectedTeam)?.coachName}
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card title="Week Management">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Advance the current week to the next week. This will start a new tracking period for all players.
          </p>
          <Button onClick={handleAdvanceWeek} variant="outline">
            Advance Week
          </Button>
        </div>
      </Card>

      <Card title="Export Data">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Export team data for analysis or reporting.
          </p>
          <Button variant="outline" onClick={() => alert('Export functionality coming soon')}>
            Export CSV
          </Button>
        </div>
      </Card>
    </div>
  )
}

