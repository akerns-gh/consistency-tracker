import { Player } from '../../../services/adminApi'
import Button from '../../ui/Button'

interface PlayerCardProps {
  player: Player
  onEdit: (player: Player) => void
  onInvite: (player: Player) => void
  onDeactivate: (player: Player) => void
}

export default function PlayerCard({ player, onEdit, onInvite, onDeactivate }: PlayerCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800">{player.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{player.email || 'No email'}</p>
          <div className="mt-2 flex items-center space-x-2">
            <span
              className={`px-2 py-1 rounded text-xs ${
                player.isActive
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {player.isActive ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={() => onEdit(player)}>
            Edit
          </Button>
          {player.isActive && (
            <Button variant="outline" size="sm" onClick={() => onInvite(player)}>
              Invite
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => onDeactivate(player)}>
            {player.isActive ? 'Deactivate' : 'Activate'}
          </Button>
        </div>
      </div>
    </div>
  )
}

