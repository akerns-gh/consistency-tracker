import { useState } from 'react'
import NavBar from '../components/admin/NavBar'
import TabNavigation, { AdminTab } from '../components/admin/TabNavigation'
import AdminMenu from '../components/admin/AdminMenu'
import PlayerList from '../components/admin/players/PlayerList'
import ActivityList from '../components/admin/activities/ActivityList'
import SummaryCards from '../components/admin/overview/SummaryCards'
import SettingsForm from '../components/admin/settings/SettingsForm'
import TeamManagement from '../components/admin/teams/TeamManagement'
import ClubManagement from '../components/admin/clubs/ClubManagement'

export default function AppAdminDashboard() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<AdminTab>('overview')

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
        return (
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Platform Administration</h1>
            <p className="text-gray-600 mt-2">Manage all clubs and platform settings</p>
          </div>
        )
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
        {activeTab === 'overview' && (
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Platform Administration</h1>
            <p className="text-gray-600 mt-2">Manage all clubs and platform settings</p>
          </div>
        )}
        {activeTab === 'overview' ? (
          <>
            {renderTabContent()}
            <div className="mt-6">
              <ClubManagement />
            </div>
          </>
        ) : (
          renderTabContent()
        )}
      </main>
    </div>
  )
}

