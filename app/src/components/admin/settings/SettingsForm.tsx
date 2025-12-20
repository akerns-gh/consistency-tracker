import { useState, useEffect } from 'react'
import { createClub, createTeam, getTeams, Team, advanceWeek } from '../../../services/adminApi'
import { useAuth } from '../../../contexts/AuthContext'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Loading from '../../ui/Loading'

export default function SettingsForm() {
  const { isAppAdmin } = useAuth()
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [clubBootstrapName, setClubBootstrapName] = useState('')
  const [clubBootstrapCreatedId, setClubBootstrapCreatedId] = useState<string | null>(null)
  const [clubBootstrapError, setClubBootstrapError] = useState<string | null>(null)
  const [teamCreateName, setTeamCreateName] = useState('')
  const [teamCreateCoachName, setTeamCreateCoachName] = useState('')
  const [teamCreateError, setTeamCreateError] = useState<string | null>(null)
  const [teamLoadError, setTeamLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setTeamLoadError(null)
      const teamsData = await getTeams()
      setTeams(teamsData.teams || [])
      if (teamsData.teams && teamsData.teams.length > 0) {
        setSelectedTeam(teamsData.teams[0].teamId)
      }
    } catch (err) {
      console.error('Failed to load settings data:', err)
      setTeams([])
      setSelectedTeam('')
      setTeamLoadError((err as any)?.message || 'Failed to load teams')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateClub = async () => {
    setClubBootstrapError(null)
    setClubBootstrapCreatedId(null)
    const name = clubBootstrapName.trim()
    if (!name) {
      setClubBootstrapError('Please enter a club name')
      return
    }

    try {
      const res = await createClub({ clubName: name })
      setClubBootstrapCreatedId(res.club.clubId)
    } catch (err: any) {
      setClubBootstrapError(err?.message || 'Failed to create club')
    }
  }

  const handleCreateTeam = async () => {
    setTeamCreateError(null)
    const name = teamCreateName.trim()
    if (!name) {
      setTeamCreateError('Please enter a team name')
      return
    }

    try {
      await createTeam({ teamName: name, coachName: teamCreateCoachName.trim() || undefined })
      setTeamCreateName('')
      setTeamCreateCoachName('')
      await loadData()
    } catch (err: any) {
      setTeamCreateError(err?.message || 'Failed to create team')
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

  const needsClubAssociation =
    !!teamLoadError &&
    (teamLoadError.includes('User not associated with a club') ||
      teamLoadError.includes('403') ||
      teamLoadError.toLowerCase().includes('access denied') ||
      teamLoadError.toLowerCase().includes('forbidden'))

  return (
    <div className="space-y-6">
      {isAppAdmin && (
        <Card title="Club Setup">
          <div className="space-y-4">
            <p className="text-sm text-gray-700">
              Your admin user is authenticated, but not associated with a club yet, so teams/players/activities can’t load.
              Create a club below, then set your Cognito user attribute <code>custom:clubId</code> to the new clubId and
              sign out/in.
            </p>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Club name</label>
              <input
                type="text"
                value={clubBootstrapName}
                onChange={(e) => setClubBootstrapName(e.target.value)}
                placeholder="e.g. True Lacrosse"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            {clubBootstrapError && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                {clubBootstrapError}
              </div>
            )}

            {clubBootstrapCreatedId ? (
              <div className="bg-green-50 border border-green-200 text-green-900 px-4 py-3 rounded space-y-2">
                <div>
                  <strong>Club created.</strong> Your clubId is:
                </div>
                <div className="font-mono break-all">{clubBootstrapCreatedId}</div>
                <div className="text-sm">
                  Next: In Cognito user pool <code>us-east-1_1voH0LIGL</code>, edit your user and set{' '}
                  <code>custom:clubId</code> to the value above, then sign out and sign back in.
                </div>
              </div>
            ) : (
              <Button onClick={handleCreateClub}>Create Club</Button>
            )}
          </div>
        </Card>
      )}

      <Card title="Team Information">
        <div className="space-y-4">
          {needsClubAssociation ? (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
              <p className="text-sm">
                <strong>Club association required:</strong> You must be associated with a club before creating teams.
                {isAppAdmin ? (
                  <> Create a club above, then set your Cognito user attribute <code>custom:clubId</code> to the clubId and sign out/in.</>
                ) : (
                  <> Please contact an administrator to associate your account with a club.</>
                )}
              </p>
            </div>
          ) : teams.length === 0 ? (
            // Show create team form when no teams exist AND user has club
            <div className="space-y-4">
              <p className="text-sm text-gray-700">
                No teams exist in your club yet. Create your first team so you can add players and team-scoped activities.
              </p>

              {teamCreateError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                  {teamCreateError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Team name</label>
                  <input
                    type="text"
                    value={teamCreateName}
                    onChange={(e) => setTeamCreateName(e.target.value)}
                    placeholder="e.g. 2028 Boys"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Coach name (optional)</label>
                  <input
                    type="text"
                    value={teamCreateCoachName}
                    onChange={(e) => setTeamCreateCoachName(e.target.value)}
                    placeholder="e.g. Coach Adams"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>

              <Button onClick={handleCreateTeam}>Create Team</Button>
            </div>
          ) : (
            // Show dropdown when teams exist
            <>
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
            </>
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

