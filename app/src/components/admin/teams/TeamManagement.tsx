import { useState, useEffect, useMemo } from 'react'
import { getTeams, createTeam, updateTeam, getTeamCoaches, addTeamCoach, removeTeamCoach, Team, Coach } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Loading from '../../ui/Loading'

type SortColumn = 'teamName' | 'teamId' | 'createdAt'
type SortDirection = 'asc' | 'desc'

export default function TeamManagement() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set())
  const [coachesByTeam, setCoachesByTeam] = useState<Record<string, Coach[]>>({})
  const [loadingCoaches, setLoadingCoaches] = useState<Set<string>>(new Set())
  
  // Search and sort state
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<SortColumn>('teamName')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  
  // Form state
  const [teamName, setTeamName] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  
  // Coach form state (per team)
  const [coachForms, setCoachForms] = useState<Record<string, { email: string; password: string }>>({})
  const [coachErrors, setCoachErrors] = useState<Record<string, string>>({})
  const [submittingCoach, setSubmittingCoach] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadTeams()
  }, [])

  const loadTeams = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getTeams()
      setTeams(data.teams || [])
    } catch (err) {
      console.error('Failed to load teams:', err)
      setError((err as any)?.message || 'Failed to load teams')
    } finally {
      setLoading(false)
    }
  }

  const loadCoachesForTeam = async (teamId: string) => {
    if (coachesByTeam[teamId]) {
      return // Already loaded
    }
    
    try {
      setLoadingCoaches(prev => new Set(prev).add(teamId))
      const data = await getTeamCoaches(teamId)
      setCoachesByTeam(prev => ({ ...prev, [teamId]: data.coaches || [] }))
    } catch (err) {
      console.error(`Failed to load coaches for team ${teamId}:`, err)
      setCoachesByTeam(prev => ({ ...prev, [teamId]: [] }))
    } finally {
      setLoadingCoaches(prev => {
        const next = new Set(prev)
        next.delete(teamId)
        return next
      })
    }
  }

  const toggleTeamExpanded = (teamId: string) => {
    setExpandedTeams(prev => {
      const next = new Set(prev)
      if (next.has(teamId)) {
        next.delete(teamId)
      } else {
        next.add(teamId)
        loadCoachesForTeam(teamId)
      }
      return next
    })
  }

  const handleCreateTeam = async () => {
    setFormError(null)
    const name = teamName.trim()
    if (!name) {
      setFormError('Please enter a team name')
      return
    }

    try {
      setSubmitting(true)
      await createTeam({ teamName: name })
      setTeamName('')
      setShowCreateForm(false)
      await loadTeams()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create team')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateTeam = async () => {
    if (!editingTeam) return
    
    setFormError(null)
    const name = teamName.trim()
    if (!name) {
      setFormError('Please enter a team name')
      return
    }

    try {
      setSubmitting(true)
      await updateTeam(editingTeam.teamId, { teamName: name })
      setEditingTeam(null)
      setTeamName('')
      await loadTeams()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to update team')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddCoach = async (teamId: string) => {
    const form = coachForms[teamId]
    if (!form) return
    
    setCoachErrors(prev => ({ ...prev, [teamId]: '' }))
    
    const email = form.email.trim()
    const password = form.password.trim()
    
    if (!email) {
      setCoachErrors(prev => ({ ...prev, [teamId]: 'Please enter an email address' }))
      return
    }
    
    if (!password) {
      setCoachErrors(prev => ({ ...prev, [teamId]: 'Please enter a temporary password' }))
      return
    }
    
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setCoachErrors(prev => ({ ...prev, [teamId]: 'Please enter a valid email address' }))
      return
    }

    try {
      setSubmittingCoach(prev => new Set(prev).add(teamId))
      await addTeamCoach(teamId, { coachEmail: email, coachPassword: password })
      
      // Clear form
      setCoachForms(prev => {
        const next = { ...prev }
        delete next[teamId]
        return next
      })
      
      // Reload coaches
      const data = await getTeamCoaches(teamId)
      setCoachesByTeam(prev => ({ ...prev, [teamId]: data.coaches || [] }))
    } catch (err: any) {
      setCoachErrors(prev => ({ ...prev, [teamId]: err?.message || 'Failed to add coach' }))
    } finally {
      setSubmittingCoach(prev => {
        const next = new Set(prev)
        next.delete(teamId)
        return next
      })
    }
  }

  const handleRemoveCoach = async (teamId: string, coachEmail: string) => {
    if (!confirm(`Are you sure you want to remove ${coachEmail} from this team?`)) {
      return
    }

    try {
      await removeTeamCoach(teamId, coachEmail)
      // Reload coaches
      const data = await getTeamCoaches(teamId)
      setCoachesByTeam(prev => ({ ...prev, [teamId]: data.coaches || [] }))
    } catch (err: any) {
      alert(err?.message || 'Failed to remove coach')
    }
  }

  const startEdit = (team: Team) => {
    setEditingTeam(team)
    setTeamName(team.teamName)
    setShowCreateForm(false)
    setFormError(null)
  }

  const cancelEdit = () => {
    setEditingTeam(null)
    setTeamName('')
    setFormError(null)
  }

  const cancelCreate = () => {
    setShowCreateForm(false)
    setTeamName('')
    setFormError(null)
  }

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const filteredAndSortedTeams = useMemo(() => {
    // Filter teams based on search term
    let filtered = teams.filter((team) => {
      const searchLower = searchTerm.toLowerCase()
      return (
        team.teamName?.toLowerCase().includes(searchLower) ||
        team.teamId?.toLowerCase().includes(searchLower)
      )
    })

    // Sort teams
    filtered.sort((a, b) => {
      let aValue: any
      let bValue: any

      switch (sortColumn) {
        case 'teamName':
          aValue = a.teamName || ''
          bValue = b.teamName || ''
          break
        case 'teamId':
          aValue = a.teamId || ''
          bValue = b.teamId || ''
          break
        case 'createdAt':
          aValue = a.createdAt ? new Date(a.createdAt).getTime() : 0
          bValue = b.createdAt ? new Date(b.createdAt).getTime() : 0
          break
        default:
          return 0
      }

      // Handle string comparison
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue)
        return sortDirection === 'asc' ? comparison : -comparison
      }

      // Handle number comparison
      const comparison = aValue - bValue
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [teams, searchTerm, sortColumn, sortDirection])

  const getSortIcon = (column: SortColumn) => {
    if (sortColumn !== column) {
      return (
        <span className="ml-1 text-gray-400">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </span>
      )
    }
    return (
      <span className="ml-1 text-primary">
        {sortDirection === 'asc' ? (
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </span>
    )
  }

  if (loading) {
    return <Loading text="Loading teams..." />
  }

  return (
    <div className="space-y-6">
      <Card title="Team Management">
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-700">
              Manage all teams in your club. Create new teams, edit existing ones, and manage coaches for each team.
            </p>
            {!showCreateForm && !editingTeam && (
              <Button onClick={() => setShowCreateForm(true)}>
                Create New Team
              </Button>
            )}
          </div>

          {/* Create/Edit Form */}
          {(showCreateForm || editingTeam) && (
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-4">
                {editingTeam ? 'Edit Team' : 'Create New Team'}
              </h3>
              
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
                  {formError}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Team Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    placeholder="e.g. 2028 Boys"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    disabled={submitting}
                  />
                </div>

                <div className="flex space-x-2">
                  <Button
                    onClick={editingTeam ? handleUpdateTeam : handleCreateTeam}
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : editingTeam ? 'Update Team' : 'Create Team'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={editingTeam ? cancelEdit : cancelCreate}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Search Bar */}
          {teams.length > 0 && (
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search teams by name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          )}

          {/* Teams List */}
          {teams.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No teams found. Create your first team to get started.</p>
            </div>
          ) : filteredAndSortedTeams.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No teams found matching your search.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredAndSortedTeams.map((team) => {
                const isExpanded = expandedTeams.has(team.teamId)
                const coaches = coachesByTeam[team.teamId] || []
                const isLoadingCoaches = loadingCoaches.has(team.teamId)
                const coachForm = coachForms[team.teamId] || { email: '', password: '' }
                const coachError = coachErrors[team.teamId] || ''
                const isSubmittingCoach = submittingCoach.has(team.teamId)
                
                return (
                  <div key={team.teamId} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                      <div className="flex-1">
                        <div className="flex items-center space-x-4">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{team.teamName}</div>
                            <div className="text-xs text-gray-500 font-mono mt-1">{team.teamId}</div>
                          </div>
                          {team.createdAt && (
                            <div className="text-xs text-gray-500">
                              Created {new Date(team.createdAt).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEdit(team)}
                          disabled={editingTeam?.teamId === team.teamId}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleTeamExpanded(team.teamId)}
                        >
                          {isExpanded ? 'Hide' : 'Manage'} Coaches
                        </Button>
                      </div>
                    </div>
                    
                    {isExpanded && (
                      <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
                        <h4 className="text-sm font-medium text-gray-700 mb-4">Coaches</h4>
                        
                        {/* Coaches List */}
                        {isLoadingCoaches ? (
                          <div className="text-sm text-gray-500 py-2">Loading coaches...</div>
                        ) : coaches.length === 0 ? (
                          <div className="text-sm text-gray-500 py-2">No coaches assigned to this team.</div>
                        ) : (
                          <div className="space-y-2 mb-4">
                            {coaches.map((coach) => (
                              <div key={coach.email} className="flex items-center justify-between bg-white px-4 py-2 rounded border border-gray-200">
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{coach.email}</div>
                                  <div className="text-xs text-gray-500">
                                    Status: {coach.status}
                                  </div>
                                </div>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRemoveCoach(team.teamId, coach.email)}
                                  className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                >
                                  Remove
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {/* Add Coach Form */}
                        <div className="border-t border-gray-300 pt-4">
                          <h5 className="text-sm font-medium text-gray-700 mb-3">Add Coach</h5>
                          {coachError && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded mb-3 text-sm">
                              {coachError}
                            </div>
                          )}
                          <div className="space-y-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Coach Email <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="email"
                                value={coachForm.email}
                                onChange={(e) => setCoachForms(prev => ({
                                  ...prev,
                                  [team.teamId]: { ...coachForm, email: e.target.value }
                                }))}
                                placeholder="coach@example.com"
                                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                disabled={isSubmittingCoach}
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Temporary Password <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="password"
                                value={coachForm.password}
                                onChange={(e) => setCoachForms(prev => ({
                                  ...prev,
                                  [team.teamId]: { ...coachForm, password: e.target.value }
                                }))}
                                placeholder="Minimum 12 characters"
                                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                disabled={isSubmittingCoach}
                              />
                              <p className="text-xs text-gray-500 mt-1">
                                Must be at least 12 characters with uppercase, lowercase, and numbers.
                              </p>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => handleAddCoach(team.teamId)}
                              disabled={isSubmittingCoach}
                            >
                              {isSubmittingCoach ? 'Adding...' : 'Add Coach'}
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

