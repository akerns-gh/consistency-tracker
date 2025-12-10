import { useState, useEffect } from 'react'
import { getReflections } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Loading from '../../ui/Loading'

export default function ReflectionHighlights() {
  const [reflections, setReflections] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReflections()
  }, [])

  const loadReflections = async () => {
    try {
      setLoading(true)
      const response = await getReflections()
      setReflections(response.reflections || [])
    } catch (err) {
      console.error('Failed to load reflections:', err)
      setReflections([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Loading text="Loading reflections..." />
  }

  return (
    <Card title="Reflection Highlights">
      {reflections.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No reflections available yet.</p>
      ) : (
        <div className="space-y-4">
          {reflections.map((reflection, index) => (
            <div key={index} className="border-b pb-4 last:border-0">
              <p className="text-sm text-gray-600 mb-2">
                <strong>{reflection.playerName}</strong> - Week {reflection.weekId}
              </p>
              <p className="text-sm text-gray-700">{reflection.wentWell}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

