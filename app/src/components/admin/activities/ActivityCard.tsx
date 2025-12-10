import { Activity } from '../../../services/adminApi'
import Button from '../../ui/Button'

interface ActivityCardProps {
  activity: Activity
  onEdit: (activity: Activity) => void
  onDelete: (activity: Activity) => void
  onToggleActive: (activity: Activity) => void
}

export default function ActivityCard({ activity, onEdit, onDelete, onToggleActive }: ActivityCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-gray-800">{activity.name}</h3>
            <span
              className={`px-2 py-1 rounded text-xs ${
                activity.isActive
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {activity.isActive ? 'Active' : 'Inactive'}
            </span>
            {activity.scope && (
              <span
                className={`px-2 py-1 rounded text-xs ${
                  activity.scope === 'club'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {activity.scope}
              </span>
            )}
          </div>
          {activity.description && (
            <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
          )}
          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
            <span>Points: {activity.pointValue}</span>
            {activity.frequency && <span>Frequency: {activity.frequency}</span>}
            {activity.activityType && <span>Type: {activity.activityType}</span>}
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={() => onEdit(activity)}>
            Edit
          </Button>
          <Button variant="outline" size="sm" onClick={() => onToggleActive(activity)}>
            {activity.isActive ? 'Deactivate' : 'Activate'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => onDelete(activity)}>
            Delete
          </Button>
        </div>
      </div>
    </div>
  )
}

