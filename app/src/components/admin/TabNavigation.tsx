import { useAuth } from '../../contexts/AuthContext'
import { useViewAsClubAdmin } from '../../contexts/ViewAsClubAdminContext'

export type AdminTab = 'players' | 'activities' | 'content' | 'overview' | 'settings' | 'teams'

interface TabNavigationProps {
  activeTab: AdminTab
  onTabChange: (tab: AdminTab) => void
}

export default function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  const { isAppAdmin } = useAuth()
  const { isViewingAsClubAdmin } = useViewAsClubAdmin()
  
  // For app_admins, hide club-specific tabs unless viewing as club admin
  const shouldShowTab = (tabId: AdminTab) => {
    if (!isAppAdmin) return true // Show all tabs for non-app-admins
    if (isViewingAsClubAdmin) return true // Show all tabs when viewing as club admin
    // For app_admins not viewing as club admin, only show overview and settings
    return tabId === 'overview' || tabId === 'settings'
  }

  const tabs: { id: AdminTab; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'players', label: 'Players', icon: '👥' },
    { id: 'activities', label: 'Activities', icon: '🏃' },
    { id: 'content', label: 'Content', icon: '📄' },
    { id: 'teams', label: 'Teams', icon: '🏆' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ].filter(tab => shouldShowTab(tab.id))

  return (
    <div className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex space-x-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

