import { useState, useEffect, useMemo } from 'react'
import { getPlayers, Player, togglePlayerActivation, invitePlayer, CsvUploadResults } from '../../../services/adminApi'
import Loading from '../../ui/Loading'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import PlayerForm from './PlayerForm'
import CsvUpload from '../csv/CsvUpload'

type SortColumn = 'firstName' | 'lastName' | 'email' | 'teamId' | 'status' | 'createdAt'
type SortDirection = 'asc' | 'desc'

// Helper function to get full name
const getFullName = (player: Player): string => {
  return `${player.firstName || ''} ${player.lastName || ''}`.trim() || 'No name'
}

export default function PlayerList() {
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null)
  const [showCsvUpload, setShowCsvUpload] = useState(false)
  const [csvSummary, setCsvSummary] = useState<CsvUploadResults | null>(null)
  
  // Sort state
  const [sortColumn, setSortColumn] = useState<SortColumn>('firstName')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  useEffect(() => {
    loadPlayers()
  }, [])

  const loadPlayers = async () => {
    try {
      setLoading(true)
      const data = await getPlayers()
      setPlayers(data.players || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load players')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    setShowForm(false)
    setEditingPlayer(null)
    loadPlayers()
  }

  const handleEdit = (player: Player) => {
    setEditingPlayer(player)
    setShowForm(true)
  }

  const handleInvite = async (player: Player) => {
    if (!player.email) {
      alert('Player must have an email address to resend verification')
      return
    }
    try {
      await invitePlayer(player.playerId, player.email)
      alert('Verification email sent successfully')
      loadPlayers()
    } catch (err: any) {
      alert(err.message || 'Failed to send verification email')
    }
  }

  const handleDeactivate = async (player: Player) => {
    const fullName = getFullName(player)
    if (!confirm(`Are you sure you want to ${player.isActive ? 'deactivate' : 'activate'} ${fullName}?`)) {
      return
    }
    try {
      await togglePlayerActivation(player.playerId)
      loadPlayers()
    } catch (err: any) {
      alert(err.message || 'Failed to update player status')
    }
  }

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const filteredAndSortedPlayers = useMemo(() => {
    // Filter players based on search term
    let filtered = players.filter((player) => {
      const searchLower = searchTerm.toLowerCase()
      return (
        player.firstName?.toLowerCase().includes(searchLower) ||
        player.lastName?.toLowerCase().includes(searchLower) ||
        player.email?.toLowerCase().includes(searchLower) ||
        player.teamId?.toLowerCase().includes(searchLower)
      )
    })

    // Sort players
    filtered.sort((a, b) => {
      let aValue: any
      let bValue: any

      switch (sortColumn) {
        case 'firstName':
          aValue = a.firstName || ''
          bValue = b.firstName || ''
          break
        case 'lastName':
          aValue = a.lastName || ''
          bValue = b.lastName || ''
          break
        case 'email':
          aValue = a.email || ''
          bValue = b.email || ''
          break
        case 'teamId':
          aValue = a.teamId || ''
          bValue = b.teamId || ''
          break
        case 'status':
          aValue = a.isActive ? 1 : 0
          bValue = b.isActive ? 1 : 0
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
  }, [players, searchTerm, sortColumn, sortDirection])

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
    return <Loading text="Loading players..." />
  }

  return (
    <div className="space-y-6">
      <Card title="Players">
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-700">
              Manage all players. Create new players, edit existing ones, or disable/enable players.
            </p>
            <div className="flex items-center space-x-2">
              {!showForm && (
                <>
                  <Button
                    onClick={() => {
                      setEditingPlayer(null)
                      setShowForm(true)
                    }}
                  >
                    Add Player
                  </Button>
                  <Button variant="outline" onClick={() => setShowCsvUpload(true)}>
                    Upload Players CSV
                  </Button>
                </>
              )}
            </div>
          </div>

          {csvSummary && (
            <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded text-sm">
              Imported players from CSV – Created: {csvSummary.summary.created}, Skipped:{' '}
              {csvSummary.summary.skipped}, Errors: {csvSummary.summary.errors}
            </div>
          )}

          {showForm && (
            <PlayerForm
              player={editingPlayer}
              onSave={handleSave}
              onCancel={() => {
                setShowForm(false)
                setEditingPlayer(null)
              }}
            />
          )}

          {/* Search Bar */}
          {players.length > 0 && (
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search players by name, email, or team..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          )}

          {/* Players Table */}
          {players.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No players found. Create your first player to get started.</p>
            </div>
          ) : filteredAndSortedPlayers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No players found matching your search.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('firstName')}
                    >
                      <div className="flex items-center">
                        First Name
                        {getSortIcon('firstName')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('lastName')}
                    >
                      <div className="flex items-center">
                        Last Name
                        {getSortIcon('lastName')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('email')}
                    >
                      <div className="flex items-center">
                        Email
                        {getSortIcon('email')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('teamId')}
                    >
                      <div className="flex items-center">
                        Team
                        {getSortIcon('teamId')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center">
                        Status
                        {getSortIcon('status')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('createdAt')}
                    >
                      <div className="flex items-center">
                        Created
                        {getSortIcon('createdAt')}
                      </div>
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAndSortedPlayers.map((player) => {
                    const isActive = player.isActive !== false && player.verificationStatus !== "pending"
                    return (
                      <tr
                        key={player.playerId}
                        className={`hover:bg-gray-50 ${!isActive ? 'opacity-60 bg-gray-50' : ''}`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{player.firstName || ''}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{player.lastName || ''}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{player.email || 'No email'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{player.teamId || 'N/A'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            {player.verificationStatus === "pending" && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                Verification Pending
                              </span>
                            )}
                            {isActive ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                Inactive
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {player.createdAt
                              ? new Date(player.createdAt).toLocaleDateString()
                              : 'N/A'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(player)}
                              disabled={editingPlayer?.playerId === player.playerId || !isActive}
                            >
                              Edit
                            </Button>
                            {isActive && player.email && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleInvite(player)}
                                disabled={!player.email}
                              >
                                Resend Verification
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeactivate(player)}
                              className={
                                isActive
                                  ? "text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                  : "text-green-600 hover:text-green-700 border-green-300 hover:border-green-400"
                              }
                            >
                              {isActive ? "Disable" : "Enable"}
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
      {showCsvUpload && (
        <CsvUpload
          type="players"
          onUploadComplete={async (results) => {
            setCsvSummary(results)
            setShowCsvUpload(false)
            await loadPlayers()
          }}
          onCancel={() => setShowCsvUpload(false)}
        />
      )}
    </div>
  )
}

