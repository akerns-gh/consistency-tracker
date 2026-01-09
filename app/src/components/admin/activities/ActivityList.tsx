import { useState, useEffect } from 'react'
import { getActivities, Activity, updateActivity, deleteActivity } from '../../../services/adminApi'
import { useViewAsClubAdmin } from '../../../contexts/ViewAsClubAdminContext'
import Loading from '../../ui/Loading'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import ActivityForm from './ActivityForm'
import ActivityCard from './ActivityCard'

export default function ActivityList() {
  const { selectedClubId, isViewingAsClubAdmin } = useViewAsClubAdmin()
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null)

  useEffect(() => {
    loadActivities()
  }, [selectedClubId, isViewingAsClubAdmin])

  const loadActivities = async () => {
    try {
      setLoading(true)
      // Pass clubId if viewing as club admin
      const clubId = isViewingAsClubAdmin ? selectedClubId : undefined
      const data = await getActivities(clubId || undefined)
      setActivities(data.activities || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load activities')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    setShowForm(false)
    setEditingActivity(null)
    loadActivities()
  }

  const handleEdit = (activity: Activity) => {
    setEditingActivity(activity)
    setShowForm(true)
  }

  const handleDelete = async (activity: Activity) => {
    if (!confirm(`Are you sure you want to delete "${activity.name}"?`)) {
      return
    }
    try {
      await deleteActivity(activity.activityId)
      loadActivities()
    } catch (err: any) {
      alert(err.message || 'Failed to delete activity')
    }
  }

  const handleToggleActive = async (activity: Activity) => {
    try {
      await updateActivity(activity.activityId, { isActive: !activity.isActive })
      loadActivities()
    } catch (err: any) {
      alert(err.message || 'Failed to update activity')
    }
  }

  if (loading) {
    return <Loading text="Loading activities..." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Activities</h2>
        <Button onClick={() => {
          setEditingActivity(null)
          setShowForm(true)
        }}>
          Add Activity
        </Button>
      </div>

      {showForm && (
        <ActivityForm
          activity={editingActivity}
          onSave={handleSave}
          onCancel={() => {
            setShowForm(false)
            setEditingActivity(null)
          }}
        />
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {activities.length === 0 ? (
        <Card>
          <div className="py-8 text-center text-gray-500">
            No activities found. Create your first activity to get started.
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {activities.map((activity) => (
            <ActivityCard
              key={activity.activityId}
              activity={activity}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onToggleActive={handleToggleActive}
            />
          ))}
        </div>
      )}
    </div>
  )
}

