import { useState, useEffect } from 'react'
import { getClubs, createClub, updateClub, disableClub, enableClub, Club } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Loading from '../../ui/Loading'

export default function ClubManagement() {
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingClub, setEditingClub] = useState<Club | null>(null)
  
  // Form state
  const [clubName, setClubName] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadClubs()
  }, [])

  const loadClubs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getClubs()
      setClubs(data.clubs || [])
    } catch (err) {
      console.error('Failed to load clubs:', err)
      setError((err as any)?.message || 'Failed to load clubs')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateClub = async () => {
    setFormError(null)
    const name = clubName.trim()
    if (!name) {
      setFormError('Please enter a club name')
      return
    }

    try {
      setSubmitting(true)
      await createClub({ clubName: name })
      setClubName('')
      setShowCreateForm(false)
      await loadClubs()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create club')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateClub = async () => {
    if (!editingClub) return
    
    setFormError(null)
    const name = clubName.trim()
    if (!name) {
      setFormError('Please enter a club name')
      return
    }

    try {
      setSubmitting(true)
      await updateClub(editingClub.clubId, { clubName: name })
      setEditingClub(null)
      setClubName('')
      await loadClubs()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to update club')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDisableClub = async (club: Club) => {
    if (!confirm(`Are you sure you want to disable "${club.clubName}"? All users will lose access immediately.`)) {
      return
    }

    try {
      await disableClub(club.clubId)
      await loadClubs()
    } catch (err: any) {
      alert(err?.message || 'Failed to disable club')
    }
  }

  const handleEnableClub = async (club: Club) => {
    if (!confirm(`Are you sure you want to enable "${club.clubName}"? Note: Users must be manually re-added to Cognito groups.`)) {
      return
    }

    try {
      await enableClub(club.clubId)
      await loadClubs()
    } catch (err: any) {
      alert(err?.message || 'Failed to enable club')
    }
  }

  const startEdit = (club: Club) => {
    setEditingClub(club)
    setClubName(club.clubName)
    setShowCreateForm(false)
    setFormError(null)
  }

  const cancelEdit = () => {
    setEditingClub(null)
    setClubName('')
    setFormError(null)
  }

  const cancelCreate = () => {
    setShowCreateForm(false)
    setClubName('')
    setFormError(null)
  }

  if (loading) {
    return <Loading text="Loading clubs..." />
  }

  return (
    <div className="space-y-6">
      <Card title="Club Management">
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-700">
              Manage all clubs in the platform. Create new clubs, edit existing ones, or disable/enable clubs.
            </p>
            {!showCreateForm && !editingClub && (
              <Button onClick={() => setShowCreateForm(true)}>
                Create New Club
              </Button>
            )}
          </div>

          {/* Create/Edit Form */}
          {(showCreateForm || editingClub) && (
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-4">
                {editingClub ? 'Edit Club' : 'Create New Club'}
              </h3>
              
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
                  {formError}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Club Name
                  </label>
                  <input
                    type="text"
                    value={clubName}
                    onChange={(e) => setClubName(e.target.value)}
                    placeholder="e.g. True Lacrosse"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    disabled={submitting}
                  />
                </div>

                <div className="flex space-x-2">
                  <Button
                    onClick={editingClub ? handleUpdateClub : handleCreateClub}
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : editingClub ? 'Update Club' : 'Create Club'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={editingClub ? cancelEdit : cancelCreate}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Clubs List */}
          {clubs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No clubs found. Create your first club to get started.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Club Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Club ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clubs
                    .sort((a, b) => {
                      // Sort: enabled clubs first, then disabled
                      const aDisabled = a.isDisabled || false
                      const bDisabled = b.isDisabled || false
                      if (aDisabled === bDisabled) return 0
                      return aDisabled ? 1 : -1
                    })
                    .map((club) => {
                      const isDisabled = club.isDisabled || false
                      return (
                        <tr
                          key={club.clubId}
                          className={`hover:bg-gray-50 ${isDisabled ? 'opacity-60 bg-gray-50' : ''}`}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{club.clubName}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500 font-mono">{club.clubId}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {isDisabled ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Disabled
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Enabled
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">
                              {club.createdAt
                                ? new Date(club.createdAt).toLocaleDateString()
                                : 'N/A'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex justify-end space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => startEdit(club)}
                                disabled={editingClub?.clubId === club.clubId || isDisabled}
                              >
                                Edit
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => isDisabled ? handleEnableClub(club) : handleDisableClub(club)}
                                className={
                                  isDisabled
                                    ? "text-green-600 hover:text-green-700 border-green-300 hover:border-green-400"
                                    : "text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                }
                              >
                                {isDisabled ? "Enable" : "Disable"}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

