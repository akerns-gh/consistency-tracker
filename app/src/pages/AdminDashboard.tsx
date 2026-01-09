import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useViewAsClubAdmin } from '../contexts/ViewAsClubAdminContext'
import { getClubs, Club } from '../services/adminApi'
import NavBar from '../components/admin/NavBar'
import TabNavigation, { AdminTab } from '../components/admin/TabNavigation'
import AdminMenu from '../components/admin/AdminMenu'
import PlayerList from '../components/admin/players/PlayerList'
import ActivityList from '../components/admin/activities/ActivityList'
import SummaryCards from '../components/admin/overview/SummaryCards'
import SettingsForm from '../components/admin/settings/SettingsForm'
import TeamManagement from '../components/admin/teams/TeamManagement'
import AppAdminDashboard from './AppAdminDashboard'
import Button from '../components/ui/Button'

export default function AdminDashboard() {
  const { isAppAdmin } = useAuth()
  const { selectedClubId, isViewingAsClubAdmin, clearViewAsClubAdmin } = useViewAsClubAdmin()
  const [viewingClub, setViewingClub] = useState<Club | null>(null)
  const navigate = useNavigate()
  
  // Load club info when viewing as club admin
  useEffect(() => {
    if (isViewingAsClubAdmin && selectedClubId) {
      loadClubInfo()
    }
  }, [isViewingAsClubAdmin, selectedClubId])

  const loadClubInfo = async () => {
    try {
      const data = await getClubs()
      const club = data.clubs.find((c: Club) => c.clubId === selectedClubId)
      setViewingClub(club || null)
    } catch (err) {
      console.error('Failed to load club info:', err)
    }
  }

  const handleStopViewing = () => {
    clearViewAsClubAdmin()
    navigate('/admin')
  }
  
  // If user is app-admin and NOT viewing as club admin, show app-admin dashboard
  if (isAppAdmin && !isViewingAsClubAdmin) {
    return <AppAdminDashboard />
  }
  const [activeTab, setActiveTab] = useState<AdminTab>('overview')
  const [menuOpen, setMenuOpen] = useState(false)

  const renderTabContent = () => {
    switch (activeTab) {
      case 'players':
        return (
          <div>
            <PlayerList />
          </div>
        )
      case 'activities':
        return (
          <div>
            <ActivityList />
          </div>
        )
      case 'content':
        return (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Content Management</h2>
            <p className="text-gray-600">Content management components will be implemented here.</p>
          </div>
        )
      case 'overview':
        return (
          <div className="space-y-6">
            <SummaryCards />
          </div>
        )
      case 'teams':
        return (
          <div>
            <TeamManagement />
          </div>
        )
      case 'settings':
        return (
          <div>
            <SettingsForm />
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar onMenuClick={() => setMenuOpen(true)} />
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      <AdminMenu
        isOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
      />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* View As Club Admin Banner */}
        {isViewingAsClubAdmin && viewingClub && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-blue-800">
                <span className="font-semibold">Viewing as club admin:</span>{' '}
                {viewingClub.clubName}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleStopViewing}
                className="text-blue-600 hover:text-blue-700 border-blue-300 hover:border-blue-400"
              >
                Stop Viewing
              </Button>
            </div>
          </div>
        )}
        {renderTabContent()}
      </main>
    </div>
  )
}

