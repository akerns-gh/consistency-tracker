import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import NavBar from '../components/admin/NavBar'
import TabNavigation, { AdminTab } from '../components/admin/TabNavigation'
import AdminMenu from '../components/admin/AdminMenu'
import PlayerList from '../components/admin/players/PlayerList'
import ActivityList from '../components/admin/activities/ActivityList'
import SummaryCards from '../components/admin/overview/SummaryCards'
import Charts from '../components/admin/overview/Charts'
import ReflectionHighlights from '../components/admin/overview/ReflectionHighlights'
import SettingsForm from '../components/admin/settings/SettingsForm'
import TeamManagement from '../components/admin/teams/TeamManagement'
import AppAdminDashboard from './AppAdminDashboard'

export default function AdminDashboard() {
  const { isAppAdmin } = useAuth()
  
  // If user is app-admin, show app-admin dashboard instead
  if (isAppAdmin) {
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
            <Charts />
            <ReflectionHighlights />
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
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {renderTabContent()}
      </main>
    </div>
  )
}

