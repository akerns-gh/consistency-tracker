import React, { useState, useEffect } from 'react'
import { Activity, createActivity, updateActivity } from '../../../services/adminApi'
import Button from '../../ui/Button'

interface ActivityFormProps {
  activity?: Activity | null
  onSave: () => void
  onCancel: () => void
}

export default function ActivityForm({ activity, onSave, onCancel }: ActivityFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [pointValue, setPointValue] = useState(1)
  const [frequency, setFrequency] = useState('daily')
  const [isActive, setIsActive] = useState(true)
  const [scope, setScope] = useState<'club' | 'team'>('team')
  const [activityType, setActivityType] = useState<'flyout' | 'link'>('flyout')
  const [contentSlug, setContentSlug] = useState('')
  const [flyoutContent, setFlyoutContent] = useState('')
  const [activityGoal, setActivityGoal] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (activity) {
      setName(activity.name)
      setDescription(activity.description || '')
      setPointValue(activity.pointValue)
      setFrequency(activity.frequency || 'daily')
      setIsActive(activity.isActive)
      setScope(activity.scope || 'team')
      setActivityType(activity.activityType || 'flyout')
      setContentSlug(activity.contentSlug || '')
      setFlyoutContent(activity.flyoutContent || '')
      setActivityGoal(activity.activityGoal || '')
    }
  }, [activity])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const activityData: Partial<Activity> = {
        name,
        description,
        pointValue,
        frequency,
        isActive,
        scope,
        activityType,
        contentSlug: activityType === 'link' ? contentSlug : undefined,
        flyoutContent: activityType === 'flyout' ? flyoutContent : undefined,
        activityGoal,
      }

      if (activity) {
        await updateActivity(activity.activityId, activityData)
      } else {
        await createActivity(activityData)
      }
      onSave()
    } catch (err: any) {
      setError(err.message || 'Failed to save activity')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 my-8">
        <h2 className="text-xl font-bold mb-4">
          {activity ? 'Edit Activity' : 'Add New Activity'}
        </h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Point Value *
              </label>
              <input
                type="number"
                value={pointValue}
                onChange={(e) => setPointValue(parseInt(e.target.value) || 1)}
                min="1"
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="daily">Daily</option>
                <option value="3x/week">3x per week</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Scope
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as 'club' | 'team')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="team">Team</option>
                <option value="club">Club</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Activity Type
              </label>
              <select
                value={activityType}
                onChange={(e) => setActivityType(e.target.value as 'flyout' | 'link')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="flyout">Flyout (HTML content)</option>
                <option value="link">Link (content page)</option>
              </select>
            </div>
          </div>

          {activityType === 'link' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content Slug
              </label>
              <input
                type="text"
                value={contentSlug}
                onChange={(e) => setContentSlug(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          )}

          {activityType === 'flyout' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Flyout Content (HTML)
              </label>
              <textarea
                value={flyoutContent}
                onChange={(e) => setFlyoutContent(e.target.value)}
                rows={6}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent font-mono text-sm"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Activity Goal (e.g., "8+ hrs", "20 mins")
            </label>
            <input
              type="text"
              value={activityGoal}
              onChange={(e) => setActivityGoal(e.target.value)}
              placeholder="8+ hrs"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
            />
            <label htmlFor="isActive" className="ml-2 block text-sm text-gray-700">
              Active
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : activity ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

