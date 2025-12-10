import { Link } from 'react-router-dom'
import { AdminTab } from './TabNavigation'

interface AdminMenuProps {
  isOpen: boolean
  onClose: () => void
  activeTab: AdminTab
  onTabChange: (tab: AdminTab) => void
}

export default function AdminMenu({ isOpen, onClose, activeTab, onTabChange }: AdminMenuProps) {
  const appPages = [
    { path: '/player', label: 'My Week', icon: '📅' },
    { path: '/player/progress', label: 'My Progress', icon: '📊' },
    { path: '/player/leaderboard', label: 'Leaderboard', icon: '🏆' },
    { path: '/player/reflection', label: 'Reflection', icon: '💭' },
    { path: '/player/resource-list', label: 'Resources', icon: '📚' },
  ]

  const adminTabs: { id: AdminTab; label: string; icon: string }[] = [
    { id: 'players', label: 'Players', icon: '👥' },
    { id: 'activities', label: 'Activities', icon: '🏃' },
    { id: 'content', label: 'Content', icon: '📄' },
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  const handleTabClick = (tab: AdminTab) => {
    onTabChange(tab)
    onClose()
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Side Menu */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 h-full overflow-y-auto">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="mb-6 text-gray-500 hover:text-gray-700"
            aria-label="Close menu"
          >
            ✕
          </button>

          {/* App Pages Section */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">App Pages</h3>
            <nav className="space-y-1">
              {appPages.map((page) => (
                <Link
                  key={page.path}
                  to={page.path}
                  onClick={onClose}
                  className="flex items-center space-x-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <span className="text-lg">{page.icon}</span>
                  <span className="text-gray-700">{page.label}</span>
                </Link>
              ))}
            </nav>
          </div>

          {/* Admin Dashboard Section */}
          <div className="border-t pt-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Admin Dashboard</h3>
            <nav className="space-y-1">
              {adminTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary bg-opacity-10 text-primary'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>
    </>
  )
}

