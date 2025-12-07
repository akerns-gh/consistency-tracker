import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getPlayer, getWeek, saveReflection } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function ReflectionView() {
  const { uniqueLink } = useParams<{ uniqueLink: string }>()
  const [player, setPlayer] = useState<any>(null)
  const [weekData, setWeekData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  
  const [wentWell, setWentWell] = useState('')
  const [doBetter, setDoBetter] = useState('')
  const [planForWeek, setPlanForWeek] = useState('')

  useEffect(() => {
    if (!uniqueLink) return
    
    loadData()
  }, [uniqueLink])

  const loadData = async () => {
    try {
      setLoading(true)
      const playerData = await getPlayer(uniqueLink!)
      setPlayer(playerData.player)
      
      const currentWeekId = playerData.currentWeek.weekId
      const week = await getWeek(uniqueLink!, currentWeekId)
      setWeekData(week)
      
      // Load existing reflection if available
      if (week.reflection) {
        setWentWell(week.reflection.wentWell || '')
        setDoBetter(week.reflection.doBetter || '')
        setPlanForWeek(week.reflection.planForWeek || '')
      }
    } catch (err: any) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!uniqueLink || !weekData) return
    
    try {
      setSaving(true)
      await saveReflection(
        uniqueLink,
        weekData.weekId,
        wentWell,
        doBetter,
        planForWeek
      )
      alert('Reflection saved successfully!')
    } catch (err: any) {
      alert('Failed to save reflection. Please try again.')
      console.error('Failed to save reflection:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading || !player) {
    return <Loading text="Loading reflection..." />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Weekly Reflection</h1>
            {weekData && (
              <p className="text-sm text-gray-600">Week {weekData.weekId}</p>
            )}
          </div>
          <button
            onClick={() => setMenuOpen(true)}
            className="text-gray-600 hover:text-gray-800"
            aria-label="Open menu"
          >
            ☰
          </button>
        </div>
      </header>

      <NavigationMenu player={player} isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <Card>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What went well this week?
              </label>
              <textarea
                value={wentWell}
                onChange={(e) => setWentWell(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                rows={4}
                placeholder="Reflect on what went well..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What could I do better?
              </label>
              <textarea
                value={doBetter}
                onChange={(e) => setDoBetter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                rows={4}
                placeholder="Think about areas for improvement..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plan for next week
              </label>
              <textarea
                value={planForWeek}
                onChange={(e) => setPlanForWeek(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                rows={4}
                placeholder="Set goals and plans for the upcoming week..."
              />
            </div>

            <div className="flex justify-end">
              <Button
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Reflection'}
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  )
}

