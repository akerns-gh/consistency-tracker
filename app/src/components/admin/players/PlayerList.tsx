import { useState, useEffect } from 'react'
import { getPlayers, Player, togglePlayerActivation, invitePlayer, CsvUploadResults } from '../../../services/adminApi'
import Loading from '../../ui/Loading'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import PlayerForm from './PlayerForm'
import PlayerCard from './PlayerCard'
import CsvUpload from '../csv/CsvUpload'

export default function PlayerList() {
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null)
  const [showCsvUpload, setShowCsvUpload] = useState(false)
  const [csvSummary, setCsvSummary] = useState<CsvUploadResults | null>(null)

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
      alert('Player must have an email address to invite')
      return
    }
    try {
      await invitePlayer(player.playerId, player.email)
      alert('Invitation sent successfully')
      loadPlayers()
    } catch (err: any) {
      alert(err.message || 'Failed to send invitation')
    }
  }

  const handleDeactivate = async (player: Player) => {
    if (!confirm(`Are you sure you want to ${player.isActive ? 'deactivate' : 'activate'} ${player.name}?`)) {
      return
    }
    try {
      await togglePlayerActivation(player.playerId)
      loadPlayers()
    } catch (err: any) {
      alert(err.message || 'Failed to update player status')
    }
  }

  const filteredPlayers = players.filter((player) =>
    player.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    player.email?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <Loading text="Loading players..." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-gray-800">Players</h2>
        <div className="flex items-center space-x-2">
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

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search players..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {filteredPlayers.length === 0 ? (
        <Card>
          <div className="py-8 text-center text-gray-500">
            {searchTerm ? 'No players found matching your search.' : 'No players found.'}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPlayers.map((player) => (
            <PlayerCard
              key={player.playerId}
              player={player}
              onEdit={handleEdit}
              onInvite={handleInvite}
              onDeactivate={handleDeactivate}
            />
          ))}
        </div>
      )}
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

